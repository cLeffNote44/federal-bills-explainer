import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills } from "@/lib/db/schema";
import { semanticSearchQuery } from "@/lib/validators";
import { sql, inArray } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const params = Object.fromEntries(request.nextUrl.searchParams);
    const query = semanticSearchQuery.parse(params);

    const offset = (query.page - 1) * query.pageSize;

    // Use Postgres full-text search with weighted ranking
    const matchResults = await db.execute<{ bill_id: string; rank: number }>(
      sql`SELECT * FROM search_bills_fts(${query.q}, ${query.pageSize}, ${offset})`
    );

    if (!matchResults.length) {
      return NextResponse.json({
        bills: [],
        total: 0,
        page: query.page,
        pageSize: query.pageSize,
      });
    }

    const billIds = matchResults.map((r) => r.bill_id);
    const rankMap = new Map(matchResults.map((r) => [r.bill_id, r.rank]));

    // Fetch full bill data
    const billRows = await db
      .select()
      .from(bills)
      .where(inArray(bills.id, billIds));

    // Sort by rank
    const sortedBills = billRows
      .map((bill) => ({
        ...bill,
        searchRank: rankMap.get(bill.id) ?? 0,
      }))
      .sort((a, b) => b.searchRank - a.searchRank);

    return NextResponse.json({
      bills: sortedBills,
      total: sortedBills.length,
      page: query.page,
      pageSize: query.pageSize,
    });
  } catch (error) {
    console.error("Error in search:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
