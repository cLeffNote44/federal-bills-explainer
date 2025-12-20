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

interface SavedBill {
  id: string;
  congress: number;
  bill_type: string;
  number: number;
  title: string;
  status: string | null;
  public_law_number: string | null;
  bookmark_id: string;
  bookmarked_at: string;
  notes: string | null;
  folder: string | null;
}

export default function SavedBillsPage() {
  const { user, token } = useAuth();
  const [bills, setBills] = useState<SavedBill[]>([]);
  const [folders, setFolders] = useState<string[]>([]);
  const [selectedFolder, setSelectedFolder] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (user && token) {
      loadSavedBills();
      loadFolders();
    } else {
      setLoading(false);
    }
  }, [user, token, selectedFolder]);

  async function loadSavedBills() {
    try {
      setLoading(true);
      setError(null);
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const params = selectedFolder ? `?folder=${encodeURIComponent(selectedFolder)}` : '';

      const response = await fetch(`${apiBase}/bookmarks${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load saved bills');
      }

      const data = await response.json();
      setBills(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load saved bills');
    } finally {
      setLoading(false);
    }
  }

  async function loadFolders() {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/bookmarks/folders`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setFolders(data);
      }
    } catch (err) {
      // Silently fail for folders
    }
  }

  async function removeBookmark(congress: number, billType: string, number: number) {
    try {
      const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${apiBase}/bookmarks/${congress}/${billType}/${number}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        setBills(bills.filter(b =>
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
                d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
              />
            </svg>
            <h1 className="mt-4 text-2xl font-bold text-gray-900 dark:text-white">
              Save Bills for Later
            </h1>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
              Sign in to save bills and access them from any device.
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
      <Header showBackLink title="Saved Bills" subtitle="" />

      <main>
        <Container className="py-8">
          {/* Folder Filter */}
          {folders.length > 0 && (
            <div className="mb-6">
              <div className="flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedFolder(null)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    !selectedFolder
                      ? 'bg-fed-blue text-white'
                      : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                  }`}
                >
                  All
                </button>
                {folders.map(folder => (
                  <button
                    key={folder}
                    onClick={() => setSelectedFolder(folder)}
                    className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                      selectedFolder === folder
                        ? 'bg-fed-blue text-white'
                        : 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-700'
                    }`}
                  >
                    {folder}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Error Alert */}
          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              onRetry={loadSavedBills}
              className="mb-8"
            />
          )}

          {/* Loading State */}
          {loading ? (
            <BillListSkeleton count={6} />
          ) : bills.length === 0 ? (
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
                  d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                />
              </svg>
              <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
                No saved bills yet
              </h3>
              <p className="mt-2 text-gray-600 dark:text-gray-400">
                Browse bills and click the bookmark icon to save them here.
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
              {bills.map(bill => (
                <div
                  key={bill.bookmark_id}
                  className="card hover:shadow-md transition-shadow"
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

                      {bill.notes && (
                        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 italic">
                          "{bill.notes}"
                        </p>
                      )}

                      <div className="mt-2 flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                        {bill.status && (
                          <span className="capitalize">{bill.status.replace(/_/g, ' ')}</span>
                        )}
                        {bill.folder && (
                          <span className="inline-flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
                            </svg>
                            {bill.folder}
                          </span>
                        )}
                        <span>
                          Saved {new Date(bill.bookmarked_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>

                    <button
                      onClick={() => removeBookmark(bill.congress, bill.bill_type, bill.number)}
                      className="p-2 text-gray-400 hover:text-red-500 transition-colors"
                      title="Remove bookmark"
                    >
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Container>
      </main>
    </div>
  );
}
