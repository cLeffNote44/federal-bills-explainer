"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface BookmarkInput {
  billId: string;
  notes?: string;
  folder?: string;
}

export function useBookmarks(userId?: string) {
  return useQuery({
    queryKey: ["bookmarks", userId ?? null],
    enabled: !!userId,
    queryFn: async () => {
      const res = await fetch("/api/bookmarks");
      if (!res.ok) throw new Error("Failed to fetch bookmarks");
      return res.json();
    },
  });
}

export function useCreateBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: BookmarkInput) => {
      const res = await fetch("/api/bookmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(input),
      });
      if (!res.ok) throw new Error("Failed to create bookmark");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
    },
  });
}

export function useDeleteBookmark() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (billId: string) => {
      const res = await fetch(`/api/bookmarks?billId=${billId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete bookmark");
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookmarks"] });
    },
  });
}
