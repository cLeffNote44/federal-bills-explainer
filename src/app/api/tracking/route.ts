import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { billTracking, bills } from "@/lib/db/schema";
import { createTrackingBody, updateTrackingBody } from "@/lib/validators";
import { requireAuth } from "@/lib/supabase/auth-helpers";
import { eq, and } from "drizzle-orm";
import { subHours } from "date-fns";

export async function GET(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    // Check for updates request
    const sinceHours = request.nextUrl.searchParams.get("sinceHours");
    if (sinceHours) {
      return getUpdates(user!.id, Number(sinceHours));
    }

    const results = await db
      .select({
        tracking: billTracking,
        bill: bills,
      })
      .from(billTracking)
      .innerJoin(bills, eq(billTracking.billId, bills.id))
      .where(eq(billTracking.userId, user!.id))
      .orderBy(billTracking.createdAt);

    return NextResponse.json({
      tracking: results.map((r) => ({
        ...r.tracking,
        bill: r.bill,
      })),
    });
  } catch (error) {
    console.error("Error listing tracking:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const body = createTrackingBody.parse(await request.json());

    // Get bill's current status
    const bill = await db.query.bills.findFirst({
      where: eq(bills.id, body.billId),
    });

    const [tracking] = await db
      .insert(billTracking)
      .values({
        userId: user!.id,
        billId: body.billId,
        notifyOnStatusChange: body.notifyOnStatusChange,
        notifyOnVote: body.notifyOnVote,
        emailNotifications: body.emailNotifications,
        lastKnownStatus: bill?.status ?? null,
      })
      .onConflictDoUpdate({
        target: [billTracking.userId, billTracking.billId],
        set: {
          notifyOnStatusChange: body.notifyOnStatusChange,
          notifyOnVote: body.notifyOnVote,
          emailNotifications: body.emailNotifications,
        },
      })
      .returning();

    return NextResponse.json(tracking, { status: 201 });
  } catch (error) {
    console.error("Error creating tracking:", error);
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
      .delete(billTracking)
      .where(
        and(eq(billTracking.userId, user!.id), eq(billTracking.billId, billId))
      );

    return NextResponse.json({ message: "Tracking removed" });
  } catch (error) {
    console.error("Error deleting tracking:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const billId = request.nextUrl.searchParams.get("billId");
    if (!billId) {
      return NextResponse.json({ error: "billId is required" }, { status: 400 });
    }

    const body = updateTrackingBody.parse(await request.json());

    const [updated] = await db
      .update(billTracking)
      .set(body)
      .where(
        and(eq(billTracking.userId, user!.id), eq(billTracking.billId, billId))
      )
      .returning();

    if (!updated) {
      return NextResponse.json({ error: "Tracking not found" }, { status: 404 });
    }

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating tracking:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

async function getUpdates(userId: string, sinceHours: number) {
  const since = subHours(new Date(), Math.min(sinceHours, 168)); // Max 7 days

  const tracked = await db
    .select({
      tracking: billTracking,
      bill: bills,
    })
    .from(billTracking)
    .innerJoin(bills, eq(billTracking.billId, bills.id))
    .where(eq(billTracking.userId, userId));

  // Find bills whose status changed since last known
  const updates = tracked
    .filter(
      (r) =>
        r.bill.status !== r.tracking.lastKnownStatus &&
        r.bill.latestActionDate &&
        r.bill.latestActionDate >= since
    )
    .map((r) => ({
      billId: r.bill.id,
      congress: r.bill.congress,
      billType: r.bill.billType,
      number: r.bill.number,
      title: r.bill.title,
      updateType: "status_change" as const,
      oldValue: r.tracking.lastKnownStatus ?? undefined,
      newValue: r.bill.status,
      updateDate: r.bill.latestActionDate!.toISOString(),
    }));

  return NextResponse.json({ updates });
}
