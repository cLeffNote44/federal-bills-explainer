import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { comments, commentUpvotes, userProfiles } from "@/lib/db/schema";
import { createCommentBody, updateCommentBody } from "@/lib/validators";
import { requireAuth } from "@/lib/supabase/auth-helpers";
import { eq, and, count, desc, asc, isNull } from "drizzle-orm";

// GET /api/comments?billId=xxx&page=1&pageSize=20&sort=newest
export async function GET(request: NextRequest) {
  try {
    const billId = request.nextUrl.searchParams.get("billId");
    if (!billId) {
      return NextResponse.json({ error: "billId is required" }, { status: 400 });
    }

    const page = Number(request.nextUrl.searchParams.get("page") ?? "1");
    const pageSize = Math.min(
      Number(request.nextUrl.searchParams.get("pageSize") ?? "20"),
      50
    );
    const sort = request.nextUrl.searchParams.get("sort") ?? "newest";

    const orderBy = sort === "oldest" ? asc(comments.createdAt) : desc(comments.createdAt);

    // Fetch top-level comments (no parent)
    const topComments = await db
      .select({
        comment: comments,
        displayName: userProfiles.displayName,
      })
      .from(comments)
      .leftJoin(userProfiles, eq(comments.userId, userProfiles.id))
      .where(and(eq(comments.billId, billId), isNull(comments.parentId)))
      .orderBy(orderBy)
      .limit(pageSize)
      .offset((page - 1) * pageSize);

    // Get upvote counts and reply counts for each comment
    const enriched = await Promise.all(
      topComments.map(async ({ comment, displayName }) => {
        const [[upvoteResult], [replyResult]] = await Promise.all([
          db
            .select({ count: count() })
            .from(commentUpvotes)
            .where(eq(commentUpvotes.commentId, comment.id)),
          db
            .select({ count: count() })
            .from(comments)
            .where(eq(comments.parentId, comment.id)),
        ]);

        return {
          ...comment,
          displayName,
          upvoteCount: upvoteResult?.count ?? 0,
          replyCount: replyResult?.count ?? 0,
        };
      })
    );

    const [totalResult] = await db
      .select({ total: count() })
      .from(comments)
      .where(and(eq(comments.billId, billId), isNull(comments.parentId)));

    return NextResponse.json({
      comments: enriched,
      total: totalResult?.total ?? 0,
      page,
      pageSize,
    });
  } catch (error) {
    console.error("Error listing comments:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

// POST /api/comments?billId=xxx
export async function POST(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const billId = request.nextUrl.searchParams.get("billId");
    if (!billId) {
      return NextResponse.json({ error: "billId is required" }, { status: 400 });
    }

    const body = createCommentBody.parse(await request.json());

    const [comment] = await db
      .insert(comments)
      .values({
        billId,
        userId: user!.id,
        content: body.content,
        parentId: body.parentId ?? null,
      })
      .returning();

    return NextResponse.json(comment, { status: 201 });
  } catch (error) {
    console.error("Error creating comment:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

// PUT /api/comments?commentId=xxx
export async function PUT(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const commentId = request.nextUrl.searchParams.get("commentId");
    if (!commentId) {
      return NextResponse.json({ error: "commentId is required" }, { status: 400 });
    }

    const body = updateCommentBody.parse(await request.json());

    const [updated] = await db
      .update(comments)
      .set({ content: body.content, updatedAt: new Date() })
      .where(and(eq(comments.id, commentId), eq(comments.userId, user!.id)))
      .returning();

    if (!updated) {
      return NextResponse.json({ error: "Comment not found or not yours" }, { status: 404 });
    }

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating comment:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

// DELETE /api/comments?commentId=xxx
export async function DELETE(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const commentId = request.nextUrl.searchParams.get("commentId");
    if (!commentId) {
      return NextResponse.json({ error: "commentId is required" }, { status: 400 });
    }

    // Soft delete — mark as deleted but keep for thread integrity
    const [deleted] = await db
      .update(comments)
      .set({ isDeleted: true, content: "[deleted]", updatedAt: new Date() })
      .where(and(eq(comments.id, commentId), eq(comments.userId, user!.id)))
      .returning();

    if (!deleted) {
      return NextResponse.json({ error: "Comment not found or not yours" }, { status: 404 });
    }

    return NextResponse.json({ message: "Comment deleted" });
  } catch (error) {
    console.error("Error deleting comment:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
