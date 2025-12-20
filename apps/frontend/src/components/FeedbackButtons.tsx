'use client';

import { useState } from 'react';
import { api } from '@/lib/api';
import { getAuthToken, getSessionId } from '@/contexts';

interface FeedbackButtonsProps {
  explanationId: string;
  billId: string;
  className?: string;
}

type FeedbackState = 'none' | 'helpful' | 'not_helpful';

export default function FeedbackButtons({
  explanationId,
  billId,
  className = '',
}: FeedbackButtonsProps) {
  const [feedback, setFeedback] = useState<FeedbackState>('none');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showThankYou, setShowThankYou] = useState(false);
  const [showFeedbackForm, setShowFeedbackForm] = useState(false);
  const [feedbackText, setFeedbackText] = useState('');

  const submitFeedback = async (isHelpful: boolean, text?: string) => {
    setIsSubmitting(true);
    try {
      const token = getAuthToken();
      const sessionId = getSessionId();

      await api.post('feedback', {
        json: {
          explanation_id: explanationId,
          bill_id: billId,
          is_helpful: isHelpful,
          feedback_text: text,
          session_id: sessionId,
        },
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      setFeedback(isHelpful ? 'helpful' : 'not_helpful');
      setShowThankYou(true);
      setShowFeedbackForm(false);

      // Hide thank you message after 3 seconds
      setTimeout(() => setShowThankYou(false), 3000);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleThumbsUp = () => {
    if (feedback !== 'none') return;
    submitFeedback(true);
  };

  const handleThumbsDown = () => {
    if (feedback !== 'none') return;
    setShowFeedbackForm(true);
  };

  const handleSubmitNegativeFeedback = (e: React.FormEvent) => {
    e.preventDefault();
    submitFeedback(false, feedbackText);
  };

  if (showThankYou) {
    return (
      <div className={`flex items-center gap-2 text-green-600 dark:text-green-400 ${className}`}>
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
        <span className="text-sm font-medium">Thanks for your feedback!</span>
      </div>
    );
  }

  if (showFeedbackForm) {
    return (
      <div className={`${className}`}>
        <form onSubmit={handleSubmitNegativeFeedback} className="space-y-3">
          <p className="text-sm text-gray-600 dark:text-gray-300">
            How could we improve this explanation?
          </p>
          <textarea
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            placeholder="Your feedback helps us improve... (optional)"
            className="w-full px-3 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-fed-blue focus:border-transparent bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100"
            rows={3}
          />
          <div className="flex gap-2">
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-fed-blue rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? 'Sending...' : 'Submit'}
            </button>
            <button
              type="button"
              onClick={() => {
                setShowFeedbackForm(false);
                setFeedbackText('');
              }}
              className="px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    );
  }

  return (
    <div className={`flex items-center gap-4 ${className}`}>
      <span className="text-sm text-gray-500 dark:text-gray-400">
        Was this explanation helpful?
      </span>
      <div className="flex items-center gap-2">
        {/* Thumbs Up */}
        <button
          onClick={handleThumbsUp}
          disabled={feedback !== 'none' || isSubmitting}
          className={`p-2 rounded-full transition-all ${
            feedback === 'helpful'
              ? 'bg-green-100 dark:bg-green-900 text-green-600 dark:text-green-400'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-green-600 dark:hover:text-green-400'
          } disabled:cursor-not-allowed`}
          title="Helpful"
          aria-label="Mark as helpful"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
            />
          </svg>
        </button>

        {/* Thumbs Down */}
        <button
          onClick={handleThumbsDown}
          disabled={feedback !== 'none' || isSubmitting}
          className={`p-2 rounded-full transition-all ${
            feedback === 'not_helpful'
              ? 'bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-400'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-400 hover:text-red-600 dark:hover:text-red-400'
          } disabled:cursor-not-allowed`}
          title="Not helpful"
          aria-label="Mark as not helpful"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h.096c.5 0 .905-.405.905-.904 0-.715.211-1.413.608-2.008L17 13V4m-7 10h2m5-10h2a2 2 0 012 2v6a2 2 0 01-2 2h-2.5"
            />
          </svg>
        </button>
      </div>
    </div>
  );
}
