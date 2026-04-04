import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills } from "@/lib/db/schema";
import { semanticSearchQuery } from "@/lib/validators";
import { generateEmbedding } from "@/lib/ai/embed";
import { sql, inArray } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const params = Object.fromEntries(request.nextUrl.searchParams);
    const query = semanticSearchQuery.parse(params);

    // Generate embedding for the search query
    const { vector } = await generateEmbedding(query.q);

    // Use the match_bills SQL function for vector similarity search
    const vectorStr = `[${vector.join(",")}]`;
    const matchResults = await db.execute<{ bill_id: string; similarity: number }>(
      sql`SELECT * FROM match_bills(${vectorStr}::vector, 0.3, ${query.pageSize})`
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
    const similarityMap = new Map(
      matchResults.map((r) => [r.bill_id, r.similarity])
    );

    // Fetch full bill data
    const billRows = await db
      .select()
      .from(bills)
      .where(inArray(bills.id, billIds));

    // Sort by similarity score
    const sortedBills = billRows
      .map((bill) => ({
        ...bill,
        similarity: similarityMap.get(bill.id) ?? 0,
      }))
      .sort((a, b) => b.similarity - a.similarity);

    return NextResponse.json({
      bills: sortedBills,
      total: sortedBills.length,
      page: query.page,
      pageSize: query.pageSize,
    });
  } catch (error) {
    console.error("Error in semantic search:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
