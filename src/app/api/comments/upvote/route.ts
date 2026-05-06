import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { commentUpvotes } from "@/lib/db/schema";
import { requireAuth } from "@/lib/supabase/auth-helpers";
import { and, eq } from "drizzle-orm";
import { z } from "zod";

const bodySchema = z.object({
  commentId: z.string().uuid(),
});

export async function POST(request: NextRequest) {
  try {
    const { user, error: authError } = await requireAuth();
    if (authError) return authError;

    const { commentId } = bodySchema.parse(await request.json());

    await db
      .insert(commentUpvotes)
      .values({ userId: user!.id, commentId })
      .onConflictDoNothing();

    return NextResponse.json({ upvoted: true });
  } catch (error) {
    console.error("Error creating upvote:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { user, error: authError } = await requireAuth();
    if (authError) return authError;

    const commentId = request.nextUrl.searchParams.get("commentId");
    if (!commentId) {
      return NextResponse.json({ error: "commentId is required" }, { status: 400 });
    }

    await db
      .delete(commentUpvotes)
      .where(
        and(
          eq(commentUpvotes.userId, user!.id),
          eq(commentUpvotes.commentId, commentId)
        )
      );

    return NextResponse.json({ upvoted: false });
  } catch (error) {
    console.error("Error removing upvote:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
