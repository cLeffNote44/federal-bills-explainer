"use client";

import { Bookmark, BookmarkCheck, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/hooks/use-auth";
import { useCreateBookmark, useDeleteBookmark, useBookmarks } from "@/hooks/use-bookmarks";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";

interface BookmarkButtonProps {
  billId: string;
  variant?: "default" | "icon";
}

export function BookmarkButton({ billId, variant = "default" }: BookmarkButtonProps) {
  const { user } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const { data } = useBookmarks(user?.id);
  const createBookmark = useCreateBookmark();
  const deleteBookmark = useDeleteBookmark();

  const isBookmarked = data?.bookmarks?.some(
    (b: { billId: string }) => b.billId === billId
  ) ?? false;

  const isLoading = createBookmark.isPending || deleteBookmark.isPending;

  function handleClick() {
    if (!user) {
      openAuthModal("login");
      return;
    }

    if (isBookmarked) {
      deleteBookmark.mutate(billId);
    } else {
      createBookmark.mutate({ billId });
    }
  }

  if (variant === "icon") {
    return (
      <Button
        variant="ghost"
        size="icon-sm"
        onClick={handleClick}
        disabled={isLoading}
        aria-label={isBookmarked ? "Remove bookmark" : "Bookmark bill"}
        className={cn(isBookmarked && "text-primary")}
      >
        {isLoading ? (
          <Loader2 className="size-3.5 animate-spin" />
        ) : isBookmarked ? (
          <BookmarkCheck className="size-3.5" />
        ) : (
          <Bookmark className="size-3.5" />
        )}
      </Button>
    );
  }

  return (
    <Button
      variant={isBookmarked ? "secondary" : "outline"}
      size="sm"
      onClick={handleClick}
      disabled={isLoading}
      className="gap-1.5"
    >
      {isLoading ? (
        <Loader2 className="size-3.5 animate-spin" />
      ) : isBookmarked ? (
        <BookmarkCheck className="size-3.5" />
      ) : (
        <Bookmark className="size-3.5" />
      )}
      {isBookmarked ? "Saved" : "Save"}
    </Button>
  );
}
