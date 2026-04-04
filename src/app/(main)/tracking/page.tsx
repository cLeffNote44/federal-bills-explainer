"use client";

import { Container } from "@/components/layout/container";
import { BillList } from "@/components/bills/bill-list";
import { useTrackedBills } from "@/hooks/use-tracking";
import { useAuth } from "@/hooks/use-auth";
import { useUIStore } from "@/stores/ui-store";
import { Bell } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function TrackingPage() {
  const { user, loading: authLoading } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const { data, isLoading } = useTrackedBills();

  if (!authLoading && !user) {
    return (
      <Container className="flex flex-col items-center justify-center gap-4 py-24">
        <Bell className="size-10 text-muted-foreground/40" />
        <p className="text-sm text-muted-foreground">
          Sign in to track bills and get notified of changes.
        </p>
        <Button onClick={() => openAuthModal("login")}>Sign In</Button>
      </Container>
    );
  }

  const bills = data?.tracking?.map((t: { bill: unknown }) => t.bill) ?? [];

  return (
    <Container className="py-6">
      <div className="mb-6 flex items-center gap-2">
        <Bell className="size-5 text-primary" />
        <h1 className="text-xl font-bold">Tracked Bills</h1>
      </div>

      <BillList
        bills={bills}
        isLoading={authLoading || isLoading}
        emptyMessage="Not tracking any bills yet. Browse bills and track the ones you care about."
      />
    </Container>
  );
}
