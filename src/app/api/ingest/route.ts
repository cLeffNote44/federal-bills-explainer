import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { runIngestion } from "@/lib/ingestion/pipeline";
import { logger } from "@/lib/logger";
import { z } from "zod";
import { format, subDays } from "date-fns";

const ingestBody = z.object({
  fromDate: z.string().date().optional(),
  toDate: z.string().date().optional(),
  maxRecords: z.number().int().min(1).max(100).optional(),
});

export async function POST(request: NextRequest) {
  const log = logger.child({ trigger: "admin" });
  try {
    const supabase = await createClient();
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    let options;
    try {
      const body = await request.json();
      options = ingestBody.parse(body);
    } catch {
      options = {};
    }

    const toDate = options.toDate ?? format(new Date(), "yyyy-MM-dd");
    const fromDate =
      options.fromDate ?? format(subDays(new Date(), 30), "yyyy-MM-dd");
    const maxRecords = options.maxRecords ?? 20;

    log.info("Manual ingestion starting", {
      userId: user.id,
      fromDate,
      toDate,
      maxRecords,
    });

    const result = await runIngestion({ fromDate, toDate, maxRecords });

    log.info("Manual ingestion completed", { userId: user.id, ...result });

    return NextResponse.json(result);
  } catch (error) {
    log.error("Manual ingestion failed", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}
