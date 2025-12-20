'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth, getAuthToken } from '@/contexts';

interface BookmarkButtonProps {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  className?: string;
}

export default function BookmarkButton({
  billId,
  congress,
  billType,
  number,
  size = 'md',
  showLabel = false,
  className = '',
}: BookmarkButtonProps) {
  const { isAuthenticated, user } = useAuth();
  const [isBookmarked, setIsBookmarked] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const sizeClasses = {
    sm: 'p-1.5',
    md: 'p-2',
    lg: 'p-3',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  // Check if bill is bookmarked on mount
  useEffect(() => {
    if (!isAuthenticated) return;

    const checkBookmark = async () => {
      try {
        const token = getAuthToken();
        const response = await api
          .get(`bookmarks/check/${congress}/${billType}/${number}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          .json<{ is_bookmarked: boolean }>();
        setIsBookmarked(response.is_bookmarked);
      } catch {
        // Silently fail - assume not bookmarked
      }
    };

    checkBookmark();
  }, [isAuthenticated, congress, billType, number]);

  const handleClick = async () => {
    if (!isAuthenticated) {
      setShowTooltip(true);
      setTimeout(() => setShowTooltip(false), 3000);
      return;
    }

    setIsLoading(true);
    try {
      const token = getAuthToken();

      if (isBookmarked) {
        await api.delete(`bookmarks/${congress}/${billType}/${number}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setIsBookmarked(false);
      } else {
        await api.post('bookmarks', {
          headers: { Authorization: `Bearer ${token}` },
          json: {
            bill_id: billId,
            congress,
            bill_type: billType,
            number,
          },
        });
        setIsBookmarked(true);
      }
    } catch (error) {
      console.error('Failed to toggle bookmark:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={`${sizeClasses[size]} rounded-full transition-all ${
          isBookmarked
            ? 'bg-yellow-100 dark:bg-yellow-900 text-yellow-600 dark:text-yellow-400'
            : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-yellow-600 dark:hover:text-yellow-400'
        } disabled:opacity-50`}
        title={isBookmarked ? 'Remove bookmark' : 'Bookmark this bill'}
        aria-label={isBookmarked ? 'Remove bookmark' : 'Bookmark this bill'}
      >
        {isLoading ? (
          <div
            className={`${iconSizes[size]} animate-spin rounded-full border-2 border-gray-300 border-t-fed-blue`}
          />
        ) : (
          <svg
            className={iconSizes[size]}
            fill={isBookmarked ? 'currentColor' : 'none'}
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
            />
          </svg>
        )}
      </button>

      {showLabel && (
        <span className="ml-2 text-sm text-gray-600 dark:text-gray-400">
          {isBookmarked ? 'Saved' : 'Save'}
        </span>
      )}

      {/* Sign in tooltip */}
      {showTooltip && !isAuthenticated && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg shadow-lg whitespace-nowrap z-50">
          Sign in to bookmark bills
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700" />
        </div>
      )}
    </div>
  );
}
