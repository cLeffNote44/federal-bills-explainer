import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills } from "@/lib/db/schema";
import { billListQuery } from "@/lib/validators";
import { enforceRateLimit } from "@/lib/rate-limit";
import { eq, and, gte, lte, desc, asc, sql, count } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const limited = enforceRateLimit(request, {
      route: "bills:list",
      limit: 120,
      windowMs: 60_000,
    });
    if (limited) return limited;

    const params = Object.fromEntries(request.nextUrl.searchParams);
    const query = billListQuery.parse(params);

    const conditions = [];

    if (query.q) {
      conditions.push(
        sql`(${bills.title} ILIKE ${`%${query.q}%`} OR ${bills.summary} ILIKE ${`%${query.q}%`})`
      );
    }
    if (query.status) {
      conditions.push(eq(bills.status, query.status));
    }
    if (query.congress) {
      conditions.push(eq(bills.congress, query.congress));
    }
    if (query.billType) {
      conditions.push(eq(bills.billType, query.billType));
    }
    if (query.dateFrom) {
      conditions.push(gte(bills.latestActionDate, new Date(query.dateFrom)));
    }
    if (query.dateTo) {
      conditions.push(lte(bills.latestActionDate, new Date(query.dateTo)));
    }

    const where = conditions.length > 0 ? and(...conditions) : undefined;

    const orderBy = (() => {
      const dir = query.sortOrder === "asc" ? asc : desc;
      switch (query.sortBy) {
        case "congress":
          return dir(bills.congress);
        case "number":
          return dir(bills.number);
        case "date":
        default:
          return dir(bills.latestActionDate);
      }
    })();

    const offset = (query.page - 1) * query.pageSize;

    const [billRows, totalResult] = await Promise.all([
      db
        .select()
        .from(bills)
        .where(where)
        .orderBy(orderBy)
        .limit(query.pageSize)
        .offset(offset),
      db
        .select({ total: count() })
        .from(bills)
        .where(where),
    ]);

    return NextResponse.json({
      bills: billRows,
      total: totalResult[0]?.total ?? 0,
      page: query.page,
      pageSize: query.pageSize,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "ZodError") {
      return NextResponse.json({ error: "Invalid query parameters" }, { status: 400 });
    }
    console.error("Error listing bills:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
