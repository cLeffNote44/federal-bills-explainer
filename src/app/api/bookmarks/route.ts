import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { bookmarks, bills } from "@/lib/db/schema";
import { createBookmarkBody } from "@/lib/validators";
import { requireAuth } from "@/lib/supabase/auth-helpers";
import { eq, and } from "drizzle-orm";

export async function GET() {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const results = await db
      .select({
        bookmark: bookmarks,
        bill: bills,
      })
      .from(bookmarks)
      .innerJoin(bills, eq(bookmarks.billId, bills.id))
      .where(eq(bookmarks.userId, user!.id))
      .orderBy(bookmarks.createdAt);

    return NextResponse.json({
      bookmarks: results.map((r) => ({
        ...r.bookmark,
        bill: r.bill,
      })),
    });
  } catch (error) {
    console.error("Error listing bookmarks:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const body = createBookmarkBody.parse(await request.json());

    const [bookmark] = await db
      .insert(bookmarks)
      .values({
        userId: user!.id,
        billId: body.billId,
        notes: body.notes,
        folder: body.folder,
      })
      .onConflictDoUpdate({
        target: [bookmarks.userId, bookmarks.billId],
        set: {
          notes: body.notes,
          folder: body.folder,
        },
      })
      .returning();

    return NextResponse.json(bookmark, { status: 201 });
  } catch (error) {
    console.error("Error creating bookmark:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const billId = request.nextUrl.searchParams.get("billId");
    if (!billId) {
      return NextResponse.json({ error: "billId is required" }, { status: 400 });
    }

    await db
      .delete(bookmarks)
      .where(
        and(eq(bookmarks.userId, user!.id), eq(bookmarks.billId, billId))
      );

    return NextResponse.json({ message: "Bookmark removed" });
  } catch (error) {
    console.error("Error deleting bookmark:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
