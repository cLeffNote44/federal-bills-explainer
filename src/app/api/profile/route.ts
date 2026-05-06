import { NextRequest, NextResponse } from "next/server";
import { db } from "@/lib/db";
import { userProfiles } from "@/lib/db/schema";
import { updateProfileBody } from "@/lib/validators";
import { requireAuth } from "@/lib/supabase/auth-helpers";
import { eq } from "drizzle-orm";

export async function GET() {
  try {
    const { user, error } = await requireAuth();
    if (error) return error;

    const profile = await db.query.userProfiles.findFirst({
      where: eq(userProfiles.id, user!.id),
    });

    if (!profile) {
      // Auto-create empty profile on first read
      const [created] = await db
        .insert(userProfiles)
        .values({ id: user!.id })
        .onConflictDoNothing()
        .returning();
      return NextResponse.json(created ?? { id: user!.id });
    }

    return NextResponse.json(profile);
  } catch (error) {
    console.error("Error fetching profile:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function PATCH(request: NextRequest) {
  try {
    const { user, error: authError } = await requireAuth();
    if (authError) return authError;

    const body = updateProfileBody.parse(await request.json());

    const [updated] = await db
      .insert(userProfiles)
      .values({ id: user!.id, ...body })
      .onConflictDoUpdate({
        target: userProfiles.id,
        set: { ...body, updatedAt: new Date() },
      })
      .returning();

    return NextResponse.json(updated);
  } catch (error) {
    console.error("Error updating profile:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
