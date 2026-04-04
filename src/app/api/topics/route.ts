import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { billTopics } from "@/lib/db/schema";
import { count, desc } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const page = Number(request.nextUrl.searchParams.get("page") ?? "1");
    const pageSize = Math.min(
      Number(request.nextUrl.searchParams.get("pageSize") ?? "20"),
      50
    );

    // Get topics with bill counts
    const topics = await db
      .select({
        name: billTopics.topicName,
        count: count(),
      })
      .from(billTopics)
      .groupBy(billTopics.topicName)
      .orderBy(desc(count()))
      .limit(pageSize)
      .offset((page - 1) * pageSize);

    return NextResponse.json({ topics });
  } catch (error) {
    console.error("Error listing topics:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
