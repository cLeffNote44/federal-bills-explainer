import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills, explanations, billTopics } from "@/lib/db/schema";
import { billPathParams } from "@/lib/validators";
import { eq, and } from "drizzle-orm";

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ congress: string; billType: string; number: string }> }
) {
  try {
    const rawParams = await params;
    const parsed = billPathParams.parse(rawParams);

    const bill = await db.query.bills.findFirst({
      where: and(
        eq(bills.congress, parsed.congress),
        eq(bills.billType, parsed.billType),
        eq(bills.number, parsed.number)
      ),
    });

    if (!bill) {
      return NextResponse.json({ error: "Bill not found" }, { status: 404 });
    }

    // Fetch explanation and topics in parallel
    const [explanation, topics] = await Promise.all([
      db.query.explanations.findFirst({
        where: eq(explanations.billId, bill.id),
        orderBy: (exp, { desc }) => [desc(exp.version)],
      }),
      db
        .select()
        .from(billTopics)
        .where(eq(billTopics.billId, bill.id))
        .orderBy(billTopics.confidenceScore),
    ]);

    return NextResponse.json({
      ...bill,
      explanation: explanation ?? null,
      topics,
    });
  } catch (error) {
    if (error instanceof Error && error.name === "ZodError") {
      return NextResponse.json({ error: "Invalid bill parameters" }, { status: 400 });
    }
    console.error("Error fetching bill:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
