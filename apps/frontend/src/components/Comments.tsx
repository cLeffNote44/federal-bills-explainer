'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth, getAuthToken } from '@/contexts';
import { CommentsSkeleton } from './Skeleton';

interface Comment {
  id: string;
  user_id: string;
  user_name: string;
  content: string;
  created_at: string;
  upvotes: number;
  is_deleted: boolean;
  replies?: Comment[];
}

interface CommentsProps {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  className?: string;
}

export default function Comments({
  billId,
  congress,
  billType,
  number,
  className = '',
}: CommentsProps) {
  const { isAuthenticated, user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [newComment, setNewComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');

  useEffect(() => {
    fetchComments();
  }, [billId]);

  const fetchComments = async () => {
    try {
      const data = await api
        .get(`comments/${congress}/${billType}/${number}`)
        .json<Comment[]>();
      setComments(data);
    } catch {
      // Silently fail - show empty comments
      setComments([]);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitComment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim() || !isAuthenticated) return;

    setSubmitting(true);
    try {
      const token = getAuthToken();
      const created = await api
        .post(`comments/${congress}/${billType}/${number}`, {
          headers: { Authorization: `Bearer ${token}` },
          json: { content: newComment },
        })
        .json<Comment>();

      setComments([created, ...comments]);
      setNewComment('');
    } catch (error) {
      console.error('Failed to post comment:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmitReply = async (parentId: string) => {
    if (!replyContent.trim() || !isAuthenticated) return;

    setSubmitting(true);
    try {
      const token = getAuthToken();
      const created = await api
        .post(`comments/${congress}/${billType}/${number}`, {
          headers: { Authorization: `Bearer ${token}` },
          json: { content: replyContent, parent_id: parentId },
        })
        .json<Comment>();

      // Add reply to parent comment
      setComments(
        comments.map((c) =>
          c.id === parentId
            ? { ...c, replies: [...(c.replies || []), created] }
            : c
        )
      );
      setReplyContent('');
      setReplyingTo(null);
    } catch (error) {
      console.error('Failed to post reply:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleUpvote = async (commentId: string) => {
    if (!isAuthenticated) return;

    try {
      const token = getAuthToken();
      await api.post(`comments/${commentId}/upvote`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      // Optimistic update
      const updateUpvotes = (commentList: Comment[]): Comment[] =>
        commentList.map((c) =>
          c.id === commentId
            ? { ...c, upvotes: c.upvotes + 1 }
            : { ...c, replies: c.replies ? updateUpvotes(c.replies) : undefined }
        );
      setComments(updateUpvotes(comments));
    } catch {
      // Silently fail
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const renderComment = (comment: Comment, isReply = false) => (
    <div
      key={comment.id}
      className={`${isReply ? 'ml-8 mt-3' : ''} ${
        comment.is_deleted ? 'opacity-50' : ''
      }`}
    >
      <div className="flex gap-3">
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-gray-200 dark:bg-gray-700 flex items-center justify-center text-sm font-medium text-gray-600 dark:text-gray-400 flex-shrink-0">
          {comment.user_name?.[0]?.toUpperCase() || '?'}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-medium text-gray-900 dark:text-gray-100 text-sm">
              {comment.user_name}
            </span>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {formatDate(comment.created_at)}
            </span>
          </div>

          <p className="text-sm text-gray-700 dark:text-gray-300 mt-1">
            {comment.is_deleted ? (
              <em className="text-gray-400">[Comment deleted]</em>
            ) : (
              comment.content
            )}
          </p>

          {!comment.is_deleted && (
            <div className="flex items-center gap-4 mt-2">
              {/* Upvote */}
              <button
                onClick={() => handleUpvote(comment.id)}
                disabled={!isAuthenticated}
                className="flex items-center gap-1 text-xs text-gray-500 dark:text-gray-400 hover:text-fed-blue dark:hover:text-blue-400 disabled:cursor-not-allowed"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 15l7-7 7 7"
                  />
                </svg>
                {comment.upvotes > 0 && comment.upvotes}
              </button>

              {/* Reply */}
              {isAuthenticated && !isReply && (
                <button
                  onClick={() =>
                    setReplyingTo(replyingTo === comment.id ? null : comment.id)
                  }
                  className="text-xs text-gray-500 dark:text-gray-400 hover:text-fed-blue dark:hover:text-blue-400"
                >
                  Reply
                </button>
              )}
            </div>
          )}

          {/* Reply form */}
          {replyingTo === comment.id && (
            <div className="mt-3">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                placeholder="Write a reply..."
                className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-fed-blue focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                rows={2}
              />
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => handleSubmitReply(comment.id)}
                  disabled={submitting || !replyContent.trim()}
                  className="px-3 py-1 text-sm font-medium text-white bg-fed-blue rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  {submitting ? 'Posting...' : 'Reply'}
                </button>
                <button
                  onClick={() => {
                    setReplyingTo(null);
                    setReplyContent('');
                  }}
                  className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                >
                  Cancel
                </button>
              </div>
            </div>
          )}

          {/* Replies */}
          {comment.replies && comment.replies.length > 0 && (
            <div className="mt-3 border-l-2 border-gray-200 dark:border-gray-700 pl-4">
              {comment.replies.map((reply) => renderComment(reply, true))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Discussion
        </h3>
        <CommentsSkeleton count={3} />
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Discussion ({comments.length})
      </h3>

      {/* New comment form */}
      {isAuthenticated ? (
        <form onSubmit={handleSubmitComment} className="mb-6">
          <textarea
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Share your thoughts on this bill..."
            className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-fed-blue focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
            rows={3}
          />
          <div className="flex justify-between items-center mt-2">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              Be respectful and constructive
            </p>
            <button
              type="submit"
              disabled={submitting || !newComment.trim()}
              className="px-4 py-2 text-sm font-medium text-white bg-fed-blue rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {submitting ? 'Posting...' : 'Post Comment'}
            </button>
          </div>
        </form>
      ) : (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            Sign in to join the discussion
          </p>
        </div>
      )}

      {/* Comments list */}
      {comments.length === 0 ? (
        <div className="text-center py-8">
          <svg
            className="mx-auto h-12 w-12 text-gray-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
            No comments yet. Be the first to share your thoughts!
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          {comments.map((comment) => renderComment(comment))}
        </div>
      )}
    </div>
  );
}
