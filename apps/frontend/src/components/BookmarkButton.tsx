'use client';

import { useState } from 'react';

interface BookmarkButtonProps {
  billId: string;
  initialBookmarked?: boolean;
  className?: string;
}

export default function BookmarkButton({ billId, initialBookmarked = false, className = '' }: BookmarkButtonProps) {
  const [isBookmarked, setIsBookmarked] = useState(initialBookmarked);
  const [loading, setLoading] = useState(false);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const toggleBookmark = async () => {
    setLoading(true);

    try {
      if (isBookmarked) {
        // Remove bookmark
        await fetch(`${API_URL}/social/bookmarks/${billId}`, { method: 'DELETE' });
        setIsBookmarked(false);
      } else {
        // Add bookmark
        await fetch(`${API_URL}/social/bookmarks`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ bill_id: billId }),
        });
        setIsBookmarked(true);
      }
    } catch (error) {
      console.error('Bookmark error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={toggleBookmark}
      disabled={loading}
      className={`flex items-center gap-2 px-3 py-1.5 rounded-md border transition-colors ${
        isBookmarked
          ? 'bg-fed-blue text-white border-fed-blue'
          : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
      } ${className}`}
    >
      <svg
        className="h-4 w-4"
        fill={isBookmarked ? 'currentColor' : 'none'}
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
        />
      </svg>
      <span className="text-sm font-medium">{isBookmarked ? 'Bookmarked' : 'Bookmark'}</span>
    </button>
  );
}
