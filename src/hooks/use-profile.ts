"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

export interface ProfileUpdate {
  displayName?: string;
  emailNotifications?: boolean;
  notificationFrequency?: "realtime" | "daily" | "weekly";
  zipCode?: string;
  state?: string;
}

export function useProfile(userId?: string) {
  return useQuery({
    queryKey: ["profile", userId ?? null],
    enabled: !!userId,
    queryFn: async () => {
      const res = await fetch("/api/profile");
      if (!res.ok) throw new Error("Failed to fetch profile");
      return res.json();
    },
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: ProfileUpdate) => {
      const res = await fetch("/api/profile", {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!res.ok) throw new Error("Failed to update profile");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["profile"] });
    },
  });
}
