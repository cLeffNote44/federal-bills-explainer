"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface CommentInput {
  billId: string;
  content: string;
  parentId?: string;
}

export function useComments(billId: string, page = 1, sort = "newest") {
  return useQuery({
    queryKey: ["comments", billId, page, sort],
    queryFn: async () => {
      const params = new URLSearchParams({
        billId,
        page: String(page),
        sort,
      });
      const res = await fetch(`/api/comments?${params}`);
      if (!res.ok) throw new Error("Failed to fetch comments");
      return res.json();
    },
    enabled: !!billId,
  });
}

export function useCreateComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (input: CommentInput) => {
      const res = await fetch(`/api/comments?billId=${input.billId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          content: input.content,
          parentId: input.parentId,
        }),
      });
      if (!res.ok) throw new Error("Failed to create comment");
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["comments", variables.billId],
      });
    },
  });
}

export function useDeleteComment() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      commentId,
    }: {
      commentId: string;
      billId: string;
    }) => {
      const res = await fetch(`/api/comments?commentId=${commentId}`, {
        method: "DELETE",
      });
      if (!res.ok) throw new Error("Failed to delete comment");
      return res.json();
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["comments", variables.billId],
      });
    },
  });
}
