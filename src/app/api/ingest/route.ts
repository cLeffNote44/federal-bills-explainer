import { NextRequest, NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";
import { runIngestion } from "@/lib/ingestion/pipeline";
import { z } from "zod";
import { format, subDays } from "date-fns";

const ingestBody = z.object({
  fromDate: z.string().date().optional(),
  toDate: z.string().date().optional(),
  maxRecords: z.number().int().min(1).max(100).optional(),
});

export async function POST(request: NextRequest) {
  try {
    // Require authenticated user (admin check via service role)
    const supabase = await createClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();

    if (authError || !user) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // Parse optional body
    let options;
    try {
      const body = await request.json();
      options = ingestBody.parse(body);
    } catch {
      options = {};
    }

    const toDate = options.toDate ?? format(new Date(), "yyyy-MM-dd");
    const fromDate = options.fromDate ?? format(subDays(new Date(), 30), "yyyy-MM-dd");

    const result = await runIngestion({
      fromDate,
      toDate,
      maxRecords: options.maxRecords ?? 20,
    });

    return NextResponse.json(result);
  } catch (error) {
    console.error("Manual ingestion failed:", error);
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Ingestion failed" },
      { status: 500 }
    );
  }
}
