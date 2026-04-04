import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills, billTopics } from "@/lib/db/schema";
import { eq, desc, count } from "drizzle-orm";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ topic: string }> }
) {
  try {
    const { topic } = await params;
    const decodedTopic = decodeURIComponent(topic);
    const page = Number(request.nextUrl.searchParams.get("page") ?? "1");
    const pageSize = Math.min(
      Number(request.nextUrl.searchParams.get("pageSize") ?? "20"),
      50
    );

    const results = await db
      .select({
        bill: bills,
        confidence: billTopics.confidenceScore,
      })
      .from(billTopics)
      .innerJoin(bills, eq(billTopics.billId, bills.id))
      .where(eq(billTopics.topicName, decodedTopic))
      .orderBy(desc(bills.latestActionDate))
      .limit(pageSize)
      .offset((page - 1) * pageSize);

    const [totalResult] = await db
      .select({ total: count() })
      .from(billTopics)
      .where(eq(billTopics.topicName, decodedTopic));

    return NextResponse.json({
      topic: decodedTopic,
      bills: results.map((r) => ({ ...r.bill, confidence: r.confidence })),
      total: totalResult?.total ?? 0,
      page,
      pageSize,
    });
  } catch (error) {
    console.error("Error fetching topic bills:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
