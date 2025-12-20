'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/contexts';
import {
  Header,
  Container,
  ErrorAlert,
  BillListSkeleton,
} from '@/components';

interface TrackedBill {
  id: string;
  bill_id: string;
  congress: number;
  bill_type: string;
  number: number;
  title: string;
  status: string | null;
  notify_on_status_change: boolean;
  notify_on_vote: boolean;
  notify_on_amendments: boolean;
  email_notifications: boolean;
  created_at: string;
  last_checked: string | null;
}

interface BillUpdate {
  bill_id: string;
  congress: number;
  bill_type: string;
  number: number;
  title: string;
  update_type: string;
  old_value: string | null;
  new_value: string;
  update_date: string;
}

export default function TrackingPage() {
  const { user, token } = useAuth();
  const [trackedBills, setTrackedBills] = useState<TrackedBill[]>([]);
  const [updates, setUpdates] = useState<BillUpdate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showUpdates, setShowUpdates] = useState(false);

  useEffect(() => {
    if (user && token) {
      loadTrackedBills();
      loadUpdates();
    } else {
      setLoading(false);
    }
  }, [user, token]);

  async function loadTrackedBills() {
    try {
      setLoading(true);
      setError(null);
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

      const response = await fetch(`${apiBase}/tracking`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load tracked bills');
      }

      const data = await response.json();
      setTrackedBills(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load tracked bills');
    } finally {
      setLoading(false);
    }
  }

  async function loadUpdates() {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';

      const response = await fetch(`${apiBase}/tracking/updates?since_hours=168`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setUpdates(data);
      }
    } catch (err) {
      // Silently fail for updates
    }
  }

  async function stopTracking(congress: number, billType: string, number: number) {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/tracking/${congress}/${billType}/${number}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setTrackedBills(trackedBills.filter(b =>
          !(b.congress === congress && b.bill_type === billType && b.number === number)
        ));
      }
    } catch (err) {
      // Show error toast
    }
  }

  if (!user) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Header />
        <Container className="py-16 text-center">
          <div className="max-w-md mx-auto">
            <svg
              className="mx-auto h-16 w-16 text-gray-400 dark:text-gray-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1.5}
                d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
              />
            </svg>
            <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-white">
              Track Bill Updates
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Sign in to track bills and get notified when they're updated.
            </p>
            <Link
              href="/"
              className="mt-6 inline-block px-6 py-3 bg-fed-blue text-white rounded-lg font-medium hover:bg-fed-blue/90 transition-colors"
            >
              Browse Bills
            </Link>
          </div>
        </Container>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header showBackLink title="Bill Tracking" subtitle="" />

      <main>
        <Container className="py-8">
          {/* Tab Navigation */}
          <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setShowUpdates(false)}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                !showUpdates
                  ? 'border-fed-blue text-fed-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Tracked Bills ({trackedBills.length})
            </button>
            <button
              onClick={() => setShowUpdates(true)}
              className={`px-4 py-2 font-medium text-sm border-b-2 transition-colors ${
                showUpdates
                  ? 'border-fed-blue text-fed-blue'
                  : 'border-transparent text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300'
              }`}
            >
              Recent Updates
              {updates.length > 0 && (
                <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400">
                  {updates.length}
                </span>
              )}
            </button>
          </div>

          {/* Error Alert */}
          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              onRetry={loadTrackedBills}
              className="mb-8"
            />
          )}

          {/* Loading State */}
          {loading ? (
            <BillListSkeleton count={6} />
          ) : showUpdates ? (
            // Updates View
            updates.length === 0 ? (
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                  All caught up!
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  No updates in the past week for your tracked bills.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {updates.map((update, index) => (
                  <div
                    key={`${update.bill_id}-${index}`}
                    className="card border-l-4 border-l-fed-blue"
                  >
                    <Link
                      href={`/bills/${update.congress}/${update.bill_type}/${update.number}`}
                      className="block"
                    >
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-fed-blue/10 text-fed-blue">
                              {update.bill_type.toUpperCase()}-{update.number}
                            </span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400">
                              {update.update_type.replace('_', ' ')}
                            </span>
                          </div>
                          <h3 className="text-lg font-medium text-gray-900 dark:text-white line-clamp-2">
                            {update.title}
                          </h3>
                          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                            {update.old_value && (
                              <>
                                <span className="line-through">{update.old_value}</span>
                                {' → '}
                              </>
                            )}
                            <span className="font-medium">{update.new_value}</span>
                          </p>
                        </div>
                        <span className="text-sm text-gray-500 dark:text-gray-400 whitespace-nowrap">
                          {new Date(update.update_date).toLocaleDateString()}
                        </span>
                      </div>
                    </Link>
                  </div>
                ))}
              </div>
            )
          ) : (
            // Tracked Bills View
            trackedBills.length === 0 ? (
              <div className="text-center py-12">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1.5}
                    d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                  />
                </svg>
                <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                  No tracked bills yet
                </h3>
                <p className="mt-2 text-gray-600 dark:text-gray-400">
                  Click the bell icon on any bill to start tracking it.
                </p>
                <Link
                  href="/"
                  className="mt-6 inline-block px-6 py-3 bg-fed-blue text-white rounded-lg font-medium hover:bg-fed-blue/90 transition-colors"
                >
                  Browse Bills
                </Link>
              </div>
            ) : (
              <div className="space-y-4">
                {trackedBills.map(bill => (
                  <div
                    key={bill.id}
                    className="card"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <Link
                          href={`/bills/${bill.congress}/${bill.bill_type}/${bill.number}`}
                          className="block"
                        >
                          <div className="flex items-center gap-2 mb-1">
                            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-fed-blue/10 text-fed-blue dark:bg-fed-blue/20 dark:text-blue-400">
                              {bill.bill_type.toUpperCase()}-{bill.number}
                            </span>
                            <span className="text-sm text-gray-500 dark:text-gray-400">
                              {bill.congress}th Congress
                            </span>
                          </div>
                          <h3 className="text-lg font-medium text-gray-900 dark:text-white line-clamp-2 hover:text-fed-blue dark:hover:text-blue-400">
                            {bill.title}
                          </h3>
                        </Link>

                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          {bill.notify_on_status_change && (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                              <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                              Status changes
                            </span>
                          )}
                          {bill.notify_on_vote && (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                              <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                              </svg>
                              Votes
                            </span>
                          )}
                          {bill.notify_on_amendments && (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300">
                              <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                              Amendments
                            </span>
                          )}
                          {bill.email_notifications && (
                            <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400">
                              <svg className="w-3 h-3 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                              </svg>
                              Email alerts
                            </span>
                          )}
                        </div>

                        <div className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                          Tracking since {new Date(bill.created_at).toLocaleDateString()}
                          {bill.last_checked && (
                            <> · Last checked {new Date(bill.last_checked).toLocaleDateString()}</>
                          )}
                        </div>
                      </div>

                      <button
                        onClick={() => stopTracking(bill.congress, bill.bill_type, bill.number)}
                        className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                        title="Stop tracking"
                      >
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )
          )}
        </Container>
      </main>
    </div>
  );
}
