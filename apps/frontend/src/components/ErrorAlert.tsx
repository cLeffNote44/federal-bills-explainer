'use client';

import { ReactNode, useState } from 'react';

type ErrorType = 'error' | 'warning' | 'info';

interface ErrorAlertProps {
  message: string | ReactNode;
  title?: string;
  type?: ErrorType;
  onDismiss?: () => void;
  onRetry?: () => void | Promise<void>;
  className?: string;
  showIcon?: boolean;
  autoHide?: number; // Auto-hide after N seconds
}

// Map common error messages to user-friendly versions
function getFriendlyMessage(message: string): string {
  const messageMap: Record<string, string> = {
    'Failed to fetch': "We couldn't connect to the server. Please check your internet connection.",
    'Network Error': "We couldn't connect to the server. Please check your internet connection.",
    'Internal Server Error': 'Something went wrong on our end. Our team has been notified.',
    '500': 'Something went wrong on our end. Our team has been notified.',
    '404': "We couldn't find what you're looking for. It may have been moved or deleted.",
    'Not Found': "We couldn't find what you're looking for. It may have been moved or deleted.",
    '401': 'Please sign in to access this content.',
    'Unauthorized': 'Please sign in to access this content.',
    '403': "You don't have permission to access this content.",
    'Forbidden': "You don't have permission to access this content.",
    '429': "You're making requests too quickly. Please wait a moment and try again.",
    'Too Many Requests': "You're making requests too quickly. Please wait a moment and try again.",
    'timeout': 'The request took too long. Please try again.',
    'TIMEOUT': 'The request took too long. Please try again.',
  };

  // Check if any key is contained in the message
  for (const [key, value] of Object.entries(messageMap)) {
    if (message.toLowerCase().includes(key.toLowerCase())) {
      return value;
    }
  }

  return message;
}

const typeStyles: Record<ErrorType, { bg: string; border: string; text: string; icon: string }> = {
  error: {
    bg: 'bg-red-50 dark:bg-red-900/20',
    border: 'border-red-200 dark:border-red-800',
    text: 'text-red-700 dark:text-red-300',
    icon: 'text-red-400 dark:text-red-500',
  },
  warning: {
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    border: 'border-yellow-200 dark:border-yellow-800',
    text: 'text-yellow-700 dark:text-yellow-300',
    icon: 'text-yellow-400 dark:text-yellow-500',
  },
  info: {
    bg: 'bg-blue-50 dark:bg-blue-900/20',
    border: 'border-blue-200 dark:border-blue-800',
    text: 'text-blue-700 dark:text-blue-300',
    icon: 'text-blue-400 dark:text-blue-500',
  },
};

const icons: Record<ErrorType, ReactNode> = {
  error: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
        clipRule="evenodd"
      />
    </svg>
  ),
  warning: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
        clipRule="evenodd"
      />
    </svg>
  ),
  info: (
    <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
      <path
        fillRule="evenodd"
        d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
        clipRule="evenodd"
      />
    </svg>
  ),
};

export default function ErrorAlert({
  message,
  title,
  type = 'error',
  onDismiss,
  onRetry,
  className = '',
  showIcon = true,
  autoHide,
}: ErrorAlertProps) {
  const [isRetrying, setIsRetrying] = useState(false);
  const [isVisible, setIsVisible] = useState(true);

  // Auto-hide functionality
  if (autoHide && isVisible) {
    setTimeout(() => {
      setIsVisible(false);
      onDismiss?.();
    }, autoHide * 1000);
  }

  if (!isVisible) return null;

  const styles = typeStyles[type];
  const friendlyMessage =
    typeof message === 'string' ? getFriendlyMessage(message) : message;

  const handleRetry = async () => {
    if (!onRetry || isRetrying) return;
    setIsRetrying(true);
    try {
      await onRetry();
    } finally {
      setIsRetrying(false);
    }
  };

  return (
    <div
      className={`${styles.bg} ${styles.border} ${styles.text} border px-4 py-3 rounded-lg relative ${className}`}
      role="alert"
      data-testid="error-alert"
    >
      <div className="flex items-start">
        {showIcon && (
          <div className={`flex-shrink-0 ${styles.icon}`}>{icons[type]}</div>
        )}
        <div className={`flex-1 ${showIcon ? 'ml-3' : ''}`}>
          {title && <h3 className="font-medium mb-1">{title}</h3>}
          <div className="text-sm">
            {typeof friendlyMessage === 'string' ? (
              <p>{friendlyMessage}</p>
            ) : (
              friendlyMessage
            )}
          </div>
          {onRetry && (
            <button
              onClick={handleRetry}
              disabled={isRetrying}
              className={`mt-2 text-sm font-medium underline hover:no-underline disabled:opacity-50 ${
                type === 'error'
                  ? 'text-red-800 dark:text-red-200'
                  : type === 'warning'
                  ? 'text-yellow-800 dark:text-yellow-200'
                  : 'text-blue-800 dark:text-blue-200'
              }`}
            >
              {isRetrying ? 'Retrying...' : 'Try again'}
            </button>
          )}
        </div>
        {onDismiss && (
          <button
            onClick={onDismiss}
            className={`flex-shrink-0 ml-3 ${styles.icon} hover:opacity-70 transition-opacity`}
            aria-label="Dismiss"
            data-testid="error-alert-dismiss"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
}
