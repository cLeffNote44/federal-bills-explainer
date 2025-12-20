'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { useAuth, getAuthToken } from '@/contexts';

interface TrackBillButtonProps {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  size?: 'sm' | 'md' | 'lg';
  variant?: 'icon' | 'button';
  className?: string;
}

export default function TrackBillButton({
  billId,
  congress,
  billType,
  number,
  size = 'md',
  variant = 'button',
  className = '',
}: TrackBillButtonProps) {
  const { isAuthenticated } = useAuth();
  const [isTracking, setIsTracking] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);

  const sizeClasses = {
    sm: variant === 'icon' ? 'p-1.5' : 'px-3 py-1.5 text-sm',
    md: variant === 'icon' ? 'p-2' : 'px-4 py-2',
    lg: variant === 'icon' ? 'p-3' : 'px-5 py-2.5 text-lg',
  };

  const iconSizes = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  // Check tracking status on mount
  useEffect(() => {
    if (!isAuthenticated) return;

    const checkTracking = async () => {
      try {
        const token = getAuthToken();
        const response = await api
          .get(`tracking/check/${congress}/${billType}/${number}`, {
            headers: { Authorization: `Bearer ${token}` },
          })
          .json<{ is_tracking: boolean }>();
        setIsTracking(response.is_tracking);
      } catch {
        // Silently fail
      }
    };

    checkTracking();
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

      if (isTracking) {
        await api.delete(`tracking/${congress}/${billType}/${number}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        setIsTracking(false);
      } else {
        await api.post('tracking', {
          headers: { Authorization: `Bearer ${token}` },
          json: {
            bill_id: billId,
            congress,
            bill_type: billType,
            number,
          },
        });
        setIsTracking(true);
      }
    } catch (error) {
      console.error('Failed to toggle tracking:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const BellIcon = ({ filled }: { filled: boolean }) => (
    <svg
      className={iconSizes[size]}
      fill={filled ? 'currentColor' : 'none'}
      viewBox="0 0 24 24"
      stroke="currentColor"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
      />
    </svg>
  );

  if (variant === 'icon') {
    return (
      <div className={`relative inline-flex ${className}`}>
        <button
          onClick={handleClick}
          disabled={isLoading}
          className={`${sizeClasses[size]} rounded-full transition-all ${
            isTracking
              ? 'bg-fed-blue text-white'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-fed-blue dark:hover:text-blue-400'
          } disabled:opacity-50`}
          title={isTracking ? 'Stop tracking' : 'Track bill updates'}
          aria-label={isTracking ? 'Stop tracking' : 'Track bill updates'}
        >
          {isLoading ? (
            <div
              className={`${iconSizes[size]} animate-spin rounded-full border-2 border-gray-300 border-t-fed-blue`}
            />
          ) : (
            <BellIcon filled={isTracking} />
          )}
        </button>

        {showTooltip && (
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg shadow-lg whitespace-nowrap z-50">
            Sign in to track bills
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700" />
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`relative inline-flex ${className}`}>
      <button
        onClick={handleClick}
        disabled={isLoading}
        className={`${sizeClasses[size]} rounded-lg font-medium transition-all flex items-center gap-2 ${
          isTracking
            ? 'bg-fed-blue text-white hover:bg-blue-700'
            : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
        } disabled:opacity-50`}
      >
        {isLoading ? (
          <div
            className={`${iconSizes[size]} animate-spin rounded-full border-2 border-gray-300 border-t-fed-blue`}
          />
        ) : (
          <BellIcon filled={isTracking} />
        )}
        <span>{isTracking ? 'Tracking' : 'Track Updates'}</span>
      </button>

      {showTooltip && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 dark:bg-gray-700 text-white text-sm rounded-lg shadow-lg whitespace-nowrap z-50">
          Sign in to track bills
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900 dark:border-t-gray-700" />
        </div>
      )}
    </div>
  );
}
