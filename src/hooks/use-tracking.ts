"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface TrackingInput {
  billId: string;
  notifyOnStatusChange?: boolean;
  notifyOnVote?: boolean;
  emailNotifications?: boolean;
}

export function useTrackedBills() {
  return useQuery({
    queryKey: ["tracking"],
    queryFn: async () => {
      const res = await fetch("/api/tracking");
      if (!res.ok) throw new Error("Failed to fetch tracking");
      return res.json();
    },
  });
}

export function useTrackingUpdates(sinceHours = 24) {
  return useQuery({
    queryKey: ["tracking-updates", sinceHours],
    queryFn: async () => {
      const res = await fetch(`/api/tracking?sinceHours=${sinceHours}`);
      if (!res.ok) throw new Error("Failed to fetch updates");
      return res.json();
    },
  });
}

export function useTrackBill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: TrackingInput) => {
      const res = await fetch("/api/tracking", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!res.ok) throw new Error("Failed to track bill");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tracking"] });
    },
  });
}

export function useUntrackBill() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (billId: string) => {
      const res = await fetch(`/api/tracking?billId=${billId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to untrack bill");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tracking"] });
    },
  });
}
