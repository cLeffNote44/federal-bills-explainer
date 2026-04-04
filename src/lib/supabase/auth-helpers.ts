import { createClient } from "./server";
import { NextResponse } from "next/server";

/**
 * Get the authenticated user from the request.
 * Returns the user or a 401 response.
 */
export async function requireAuth() {
  const supabase = await createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    return { user: null, error: NextResponse.json({ error: "Unauthorized" }, { status: 401 }) };
  }

  return { user, error: null };
}
