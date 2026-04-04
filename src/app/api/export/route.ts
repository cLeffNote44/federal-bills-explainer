import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bills, explanations } from "@/lib/db/schema";
import { exportQuery } from "@/lib/validators";
import { eq, desc } from "drizzle-orm";

export async function GET(request: NextRequest) {
  try {
    const params = Object.fromEntries(request.nextUrl.searchParams);
    const query = exportQuery.parse(params);

    const conditions = [];
    if (query.congress) conditions.push(eq(bills.congress, query.congress));
    if (query.status) conditions.push(eq(bills.status, query.status));

    const where = conditions.length > 0 ? conditions[0] : undefined;

    const billRows = await db
      .select()
      .from(bills)
      .where(where)
      .orderBy(desc(bills.latestActionDate))
      .limit(query.limit);

    if (query.format === "csv") {
      const headers = [
        "congress",
        "bill_type",
        "number",
        "title",
        "status",
        "introduced_date",
        "public_law_number",
        "sponsor_name",
        "policy_area",
      ];
      const csvRows = billRows.map((b) =>
        [
          b.congress,
          b.billType,
          b.number,
          `"${(b.title ?? "").replace(/"/g, '""')}"`,
          b.status,
          b.introducedDate ?? "",
          b.publicLawNumber ?? "",
          `"${(b.sponsor as { name?: string })?.name ?? ""}"`,
          b.policyArea ?? "",
        ].join(",")
      );
      const csv = [headers.join(","), ...csvRows].join("\n");

      return new NextResponse(csv, {
        headers: {
          "Content-Type": "text/csv",
          "Content-Disposition": `attachment; filename="bills-export.csv"`,
        },
      });
    }

    // JSON format
    let data = billRows;
    if (query.includeExplanations) {
      const withExplanations = await Promise.all(
        billRows.map(async (bill) => {
          const explanation = await db.query.explanations.findFirst({
            where: eq(explanations.billId, bill.id),
            orderBy: (exp, { desc }) => [desc(exp.version)],
          });
          return { ...bill, explanation };
        })
      );
      data = withExplanations as typeof data;
    }

    return NextResponse.json({
      exportDate: new Date().toISOString(),
      count: data.length,
      bills: data,
    });
  } catch (error) {
    console.error("Error exporting:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
