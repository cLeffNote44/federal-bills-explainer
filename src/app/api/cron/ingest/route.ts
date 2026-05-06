import { NextRequest, NextResponse } from "next/server";
import { runIngestion } from "@/lib/ingestion/pipeline";
import { logger } from "@/lib/logger";
import { format, subDays } from "date-fns";

export async function POST(request: NextRequest) {
  const log = logger.child({ trigger: "cron" });
  try {
    const authHeader = request.headers.get("authorization");
    if (authHeader !== `Bearer ${process.env.CRON_SECRET}`) {
      log.warn("Unauthorized cron invocation");
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    const toDate = format(new Date(), "yyyy-MM-dd");
    const fromDate = format(subDays(new Date(), 30), "yyyy-MM-dd");

    log.info("Cron ingestion starting", { fromDate, toDate, maxRecords: 20 });
    const result = await runIngestion({ fromDate, toDate, maxRecords: 20 });
    log.info("Cron ingestion completed", { ...result });

    return NextResponse.json(result);
  } catch (error) {
    log.error("Cron ingestion failed", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}
