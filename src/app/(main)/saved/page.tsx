"use client";

import { Container } from "@/components/layout/container";
import { BillList } from "@/components/bills/bill-list";
import { useBookmarks } from "@/hooks/use-bookmarks";
import { useAuth } from "@/hooks/use-auth";
import { useUIStore } from "@/stores/ui-store";
import { Bookmark, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { Bill } from "@/types";

export default function SavedPage() {
  const { user, loading: authLoading } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const { data, isLoading } = useBookmarks(user?.id);

  if (authLoading) {
    return (
      <Container className="flex items-center justify-center py-24">
        <Loader2 className="size-5 animate-spin text-muted-foreground" />
      </Container>
    );
  }

  if (!user) {
    return (
      <Container className="flex flex-col items-center justify-center gap-4 py-24">
        <Bookmark className="size-10 text-muted-foreground/40" />
        <p className="text-sm text-muted-foreground">
          Sign in to save and organize bills.
        </p>
        <Button onClick={() => openAuthModal("login")}>Sign In</Button>
      </Container>
    );
  }

  const bills: Bill[] =
    data?.bookmarks?.map((b: { bill: Bill }) => b.bill) ?? [];

  return (
    <Container className="py-6">
      <div className="mb-6 flex items-center gap-2">
        <Bookmark className="size-5 text-primary" />
        <h1 className="text-xl font-bold">Saved Bills</h1>
      </div>

      <BillList
        bills={bills}
        isLoading={isLoading}
        emptyMessage="No saved bills yet. Browse and bookmark bills you want to follow."
      />
    </Container>
  );
}
