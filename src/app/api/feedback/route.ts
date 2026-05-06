import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { explanationFeedback } from "@/lib/db/schema";
import { submitFeedbackBody } from "@/lib/validators";
import { createClient } from "@/lib/supabase/server";
import { enforceRateLimit } from "@/lib/rate-limit";
import { eq, count } from "drizzle-orm";
import { sql } from "drizzle-orm";

// POST /api/feedback — submit feedback (anonymous or authenticated)
export async function POST(request: NextRequest) {
  try {
    const limited = await enforceRateLimit(request, {
      route: "feedback:post",
      limit: 20,
      windowMs: 60_000,
    });
    if (limited) return limited;

    const body = submitFeedbackBody.parse(await request.json());

    // Optionally get user if authenticated
    let userId: string | null = null;
    try {
      const supabase = await createClient();
      const { data: { user } } = await supabase.auth.getUser();
      userId = user?.id ?? null;
    } catch {
      // Anonymous is fine
    }

    const [feedback] = await db
      .insert(explanationFeedback)
      .values({
        explanationId: body.explanationId,
        userId,
        sessionId: body.sessionId ?? null,
        isHelpful: body.isHelpful,
        feedbackText: body.feedbackText ?? null,
      })
      .returning();

    return NextResponse.json(feedback, { status: 201 });
  } catch (error) {
    console.error("Error submitting feedback:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

// GET /api/feedback?explanationId=xxx — get feedback stats
export async function GET(request: NextRequest) {
  try {
    const explanationId = request.nextUrl.searchParams.get("explanationId");
    if (!explanationId) {
      return NextResponse.json({ error: "explanationId is required" }, { status: 400 });
    }

    const [stats] = await db
      .select({
        total: count(),
        helpful: count(
          sql`CASE WHEN ${explanationFeedback.isHelpful} = true THEN 1 END`
        ),
      })
      .from(explanationFeedback)
      .where(eq(explanationFeedback.explanationId, explanationId));

    const total = stats?.total ?? 0;
    const helpful = stats?.helpful ?? 0;

    return NextResponse.json({
      total,
      helpful,
      notHelpful: total - helpful,
      helpfulPercentage: total > 0 ? Math.round((helpful / total) * 100) : 0,
    });
  } catch (error) {
    console.error("Error fetching feedback stats:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
