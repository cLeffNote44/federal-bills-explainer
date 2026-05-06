"use client";

import { useState } from "react";
import {
  MessageSquare,
  ChevronUp,
  Reply,
  Trash2,
  Loader2,
  Send,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuth } from "@/hooks/use-auth";
import {
  useComments,
  useCreateComment,
  useDeleteComment,
  useToggleUpvote,
} from "@/hooks/use-comments";
import { useUIStore } from "@/stores/ui-store";
import { cn } from "@/lib/utils";
import { formatDistanceToNow } from "date-fns";
import type { CommentWithMeta } from "@/types";

interface CommentsProps {
  billId: string;
}

export function Comments({ billId }: CommentsProps) {
  const { user } = useAuth();
  const openAuthModal = useUIStore((s) => s.openAuthModal);
  const [page, setPage] = useState(1);
  const [sort, setSort] = useState("newest");
  const { data, isLoading } = useComments(billId, page, sort);
  const createComment = useCreateComment();
  const [newComment, setNewComment] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!user) {
      openAuthModal("login");
      return;
    }
    if (!newComment.trim()) return;

    createComment.mutate(
      { billId, content: newComment.trim() },
      { onSuccess: () => setNewComment("") }
    );
  }

  const comments: CommentWithMeta[] = data?.comments ?? [];
  const total = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="flex items-center gap-2 text-sm font-semibold">
          <MessageSquare className="size-4" />
          Comments
          {total > 0 && (
            <span className="text-xs font-normal text-muted-foreground">
              ({total})
            </span>
          )}
        </h2>
        <div className="flex gap-1">
          {(["newest", "oldest"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setSort(s)}
              className={cn(
                "rounded-md px-2 py-1 text-xs font-medium transition-colors",
                sort === s
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              {s.charAt(0).toUpperCase() + s.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* New comment form */}
      <form onSubmit={handleSubmit} className="space-y-2">
        <Textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder={user ? "Add a comment..." : "Sign in to comment..."}
          rows={3}
          maxLength={5000}
          onClick={() => !user && openAuthModal("login")}
          className="resize-none text-sm"
        />
        <div className="flex items-center justify-between">
          <span className="text-xs text-muted-foreground">
            {newComment.length}/5000
          </span>
          <Button
            type="submit"
            size="sm"
            disabled={!newComment.trim() || createComment.isPending}
            className="gap-1.5"
          >
            {createComment.isPending ? (
              <Loader2 className="size-3 animate-spin" />
            ) : (
              <Send className="size-3" />
            )}
            Post
          </Button>
        </div>
      </form>

      {/* Comments list */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-20 w-full rounded-lg" />
          ))}
        </div>
      ) : comments.length === 0 ? (
        <p className="py-8 text-center text-xs text-muted-foreground">
          No comments yet. Be the first to share your thoughts.
        </p>
      ) : (
        <div className="space-y-3">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              billId={billId}
              currentUserId={user?.id}
            />
          ))}
        </div>
      )}

      {/* Load more */}
      {total > page * 20 && (
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setPage((p) => p + 1)}
          className="w-full"
        >
          Load more comments
        </Button>
      )}
    </div>
  );
}

function CommentItem({
  comment,
  billId,
  currentUserId,
}: {
  comment: CommentWithMeta;
  billId: string;
  currentUserId?: string;
}) {
  const [showReply, setShowReply] = useState(false);
  const [replyText, setReplyText] = useState("");
  const createComment = useCreateComment();
  const deleteComment = useDeleteComment();
  const toggleUpvote = useToggleUpvote();
  const openAuthModal = useUIStore((s) => s.openAuthModal);

  const isOwner = currentUserId === comment.userId;
  const hasUpvoted = comment.hasUpvoted ?? false;
  const timeAgo = formatDistanceToNow(new Date(comment.createdAt), {
    addSuffix: true,
  });

  function handleReply(e: React.FormEvent) {
    e.preventDefault();
    if (!replyText.trim()) return;
    createComment.mutate(
      { billId, content: replyText.trim(), parentId: comment.id },
      {
        onSuccess: () => {
          setReplyText("");
          setShowReply(false);
        },
      }
    );
  }

  function handleDelete() {
    deleteComment.mutate({ commentId: comment.id, billId });
  }

  function handleUpvote() {
    if (!currentUserId) {
      openAuthModal("login");
      return;
    }
    toggleUpvote.mutate({ commentId: comment.id, billId, hasUpvoted });
  }

  return (
    <div
      className={cn(
        "rounded-lg border border-border bg-card p-3",
        comment.isDeleted && "opacity-60"
      )}
    >
      {/* Comment header */}
      <div className="mb-1.5 flex items-center gap-2 text-xs text-muted-foreground">
        <span className="font-medium text-foreground">
          {comment.displayName || "Anonymous"}
        </span>
        <span>{timeAgo}</span>
        {comment.updatedAt !== comment.createdAt && (
          <span className="italic">(edited)</span>
        )}
      </div>

      {/* Content */}
      <p className="text-sm leading-relaxed">{comment.content}</p>

      {/* Actions */}
      <div className="mt-2 flex items-center gap-2">
        <button
          onClick={handleUpvote}
          disabled={toggleUpvote.isPending || comment.isDeleted}
          aria-pressed={hasUpvoted}
          aria-label={hasUpvoted ? "Remove upvote" : "Upvote comment"}
          className={cn(
            "flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs transition-colors",
            hasUpvoted
              ? "bg-primary/10 text-primary"
              : "text-muted-foreground hover:text-foreground",
            (toggleUpvote.isPending || comment.isDeleted) &&
              "cursor-not-allowed opacity-60"
          )}
        >
          <ChevronUp className="size-3.5" />
          <span>{comment.upvoteCount}</span>
        </button>

        {comment.replyCount > 0 && (
          <span className="text-xs text-muted-foreground">
            {comment.replyCount} {comment.replyCount === 1 ? "reply" : "replies"}
          </span>
        )}

        {!comment.isDeleted && (
          <>
            <button
              onClick={() => setShowReply(!showReply)}
              className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
            >
              <Reply className="size-3" />
              Reply
            </button>

            {isOwner && (
              <button
                onClick={handleDelete}
                disabled={deleteComment.isPending}
                className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive"
              >
                <Trash2 className="size-3" />
                Delete
              </button>
            )}
          </>
        )}
      </div>

      {/* Reply form */}
      {showReply && (
        <form onSubmit={handleReply} className="mt-3 flex gap-2">
          <Textarea
            value={replyText}
            onChange={(e) => setReplyText(e.target.value)}
            placeholder="Write a reply..."
            rows={2}
            className="flex-1 resize-none text-sm"
          />
          <div className="flex flex-col gap-1">
            <Button
              type="submit"
              size="icon-sm"
              disabled={!replyText.trim() || createComment.isPending}
            >
              {createComment.isPending ? (
                <Loader2 className="size-3 animate-spin" />
              ) : (
                <Send className="size-3" />
              )}
            </Button>
          </div>
        </form>
      )}
    </div>
  );
}
