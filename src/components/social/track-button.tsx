"use client";

import { Bell, BellRing, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useTrackedBills, useTrackBill, useUntrackBill } from "@/hooks/use-tracking";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

interface TrackButtonProps {
  billId: string;
  variant?: "default" | "icon";
}

export function TrackButton({ billId, variant = "default" }: TrackButtonProps) {
  const { user } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const { data } = useTrackedBills(user?.id);
  const trackBill = useTrackBill();
  const untrackBill = useUntrackBill();

  const isTracking = data?.tracking?.some(
    (t: { billId: string }) => t.billId === billId
  ) ?? false;

  const isLoading = trackBill.isPending || untrackBill.isPending;

  function handleClick() {
    if (!user) {
      openAuthModal("login");
      return;
    }

    if (isTracking) {
      untrackBill.mutate(billId);
    } else {
      trackBill.mutate({ billId });
    }
  }

  if (variant === "icon") {
    return (
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={handleClick}
        disabled={isLoading}
        aria-label={isTracking ? "Stop tracking" : "Track bill"}
        className={cn(isTracking && "text-primary")}
      >
        {isLoading ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : isTracking ? (
          <BellRing className="size-3.5" />
        ) : (
          <Bell className="size-3.5" />
        )}
      </Button>
    );
  }

  return (
    <Button
      variant={isTracking ? "secondary" : "outline"}
      size="sm"
      onClick={handleClick}
      disabled={isLoading}
      className="gap-1.5"
    >
      {isLoading ? (
        <Loader2 className="size-3.5 animate-spin" />
      ) : isTracking ? (
        <BellRing className="size-3.5" />
      ) : (
        <Bell className="size-3.5" />
      )}
      {isTracking ? "Tracking" : "Track"}
    </Button>
  );
}
