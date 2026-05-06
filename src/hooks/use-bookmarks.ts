"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface BookmarkInput {
  billId: string;
  notes?: string;
  folder?: string;
}

export function useBookmarks(userId?: string, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: ["bookmarks", userId ?? null, page, pageSize],
    enabled: !!userId,
    queryFn: async () => {
      const params = new URLSearchParams({
        page: String(page),
        pageSize: String(pageSize),
      });
      const res = await fetch(`/api/bookmarks?${params}`);
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
