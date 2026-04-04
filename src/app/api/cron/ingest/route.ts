import { NextRequest, NextResponse } from "next/server";
import { runIngestion } from "@/lib/ingestion/pipeline";
import { format, subDays } from "date-fns";

export async function POST(request: NextRequest) {
  try {
    // Verify cron secret (Vercel sets this header)
    const authHeader = request.headers.get("authorization");
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 30), "yyyy-MM-dd");

    const result = await runIngestion({
      fromDate,
      toDate,
      maxRecords: 20,
    });

    return NextResponse.json(result);
  } catch (error) {
    console.error("Cron ingestion failed:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}
