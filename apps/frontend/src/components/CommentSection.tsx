'use client';

import { useState, useEffect } from 'react';

interface Comment {
  id: string;
  username: string;
  content: string;
  upvotes: number;
  downvotes: number;
  created_at: string;
  parent_id?: string;
}

interface CommentSectionProps {
  billId: string;
}

export default function CommentSection({ billId }: CommentSectionProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [sortBy, setSortBy] = useState<'top' | 'new' | 'controversial'>('top');

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchComments();
  }, [billId, sortBy]);

  const fetchComments = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/social/comments?bill_id=${billId}&sort=${sortBy}`);
      const data = await response.json();
      setComments(data);
    } catch (error) {
      console.error('Error fetching comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const postComment = async () => {
    if (!newComment.trim()) return;

    try {
      const response = await fetch(`${API_URL}/social/comments`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bill_id: billId, content: newComment }),
      });

      if (response.ok) {
        setNewComment('');
        fetchComments();
      }
    } catch (error) {
      console.error('Error posting comment:', error);
    }
  };

  const vote = async (commentId: string, voteType: 'upvote' | 'downvote') => {
    try {
      await fetch(`${API_URL}/social/comments/${commentId}/vote?vote_type=${voteType}`, {
        method: 'POST',
      });
      fetchComments();
    } catch (error) {
      console.error('Error voting:', error);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mt-8">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Comments ({comments.length})</h2>
        <div className="flex gap-2">
          <button
            onClick={() => setSortBy('top')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              sortBy === 'top' ? 'bg-fed-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            Top
          </button>
          <button
            onClick={() => setSortBy('new')}
            className={`px-3 py-1 rounded text-sm font-medium ${
              sortBy === 'new' ? 'bg-fed-blue text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            New
          </button>
        </div>
      </div>

      {/* New Comment */}
      <div className="mb-6">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-fed-blue"
          rows={3}
        />
        <button
          onClick={postComment}
          className="mt-2 px-4 py-2 bg-fed-blue text-white rounded-md font-medium hover:bg-blue-700"
        >
          Post Comment
        </button>
      </div>

      {/* Comments List */}
      {loading ? (
        <div className="text-center py-8 text-gray-500">Loading comments...</div>
      ) : comments.length === 0 ? (
        <div className="text-center py-8 text-gray-500">No comments yet. Be the first to comment!</div>
      ) : (
        <div className="space-y-4">
          {comments.map((comment) => (
            <div key={comment.id} className="border-l-2 border-gray-200 pl-4">
              <div className="flex items-start gap-3">
                <div className="flex flex-col items-center gap-1">
                  <button
                    onClick={() => vote(comment.id, 'upvote')}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    ▲
                  </button>
                  <span className="text-sm font-medium">{comment.upvotes - comment.downvotes}</span>
                  <button
                    onClick={() => vote(comment.id, 'downvote')}
                    className="p-1 hover:bg-gray-100 rounded"
                  >
                    ▼
                  </button>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-gray-900">{comment.username}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(comment.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-700">{comment.content}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
