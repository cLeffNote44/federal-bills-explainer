'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api, type Bill } from '@/lib/api';
import { Skeleton } from './Skeleton';

interface RelatedBillsProps {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  limit?: number;
  className?: string;
}

export default function RelatedBills({
  billId,
  congress,
  billType,
  number,
  limit = 5,
  className = '',
}: RelatedBillsProps) {
  const [relatedBills, setRelatedBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRelatedBills = async () => {
      setLoading(true);
      setError(null);

      try {
        // First try to get related bills from the API
        const data = await api
          .get(`bills/${congress}/${billType}/${number}/related`, {
            searchParams: { limit },
          })
          .json<Bill[]>();
        setRelatedBills(data);
      } catch {
        // If the endpoint doesn't exist, fall back to semantic search
        try {
          // Use semantic search with the bill title as query
          const data = await api
            .get('bills/search', {
              searchParams: {
                q: `similar bills congress ${congress}`,
                page_size: limit + 1, // Get one extra to exclude current bill
              },
            })
            .json<Bill[]>();

          // Filter out the current bill
          const filtered = data.filter(
            (b) =>
              !(
                b.congress === congress &&
                b.bill_type === billType &&
                b.number === number
              )
          );

          setRelatedBills(filtered.slice(0, limit));
        } catch {
          setError('Unable to find related bills');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRelatedBills();
  }, [billId, congress, billType, number, limit]);

  if (loading) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Related Bills
        </h3>
        <div className="space-y-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-3">
              <Skeleton className="w-16 h-5" />
              <Skeleton className="flex-1 h-4" variant="text" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (error || relatedBills.length === 0) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
          Related Bills
        </h3>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {error || 'No related bills found'}
        </p>
      </div>
    );
  }

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
        Related Bills
      </h3>

      <div className="space-y-3">
        {relatedBills.map((bill) => (
          <Link
            key={`${bill.congress}-${bill.bill_type}-${bill.number}`}
            href={`/bills/${bill.congress}/${bill.bill_type}/${bill.number}`}
            className="block group"
          >
            <div className="flex items-start gap-3 p-2 -mx-2 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              {/* Bill identifier badge */}
              <span className="inline-flex items-center px-2 py-1 rounded text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 flex-shrink-0">
                {bill.bill_type.toUpperCase()}-{bill.number}
              </span>

              <div className="flex-1 min-w-0">
                <p className="text-sm text-gray-900 dark:text-gray-100 line-clamp-2 group-hover:text-fed-blue dark:group-hover:text-blue-400 transition-colors">
                  {bill.title}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                  Congress {bill.congress}
                  {bill.public_law_number && (
                    <span className="ml-2 text-green-600 dark:text-green-400">
                      Became law
                    </span>
                  )}
                </p>
              </div>

              {/* Arrow icon */}
              <svg
                className="w-4 h-4 text-gray-400 group-hover:text-fed-blue dark:group-hover:text-blue-400 flex-shrink-0 transition-colors"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </div>
          </Link>
        ))}
      </div>

      {relatedBills.length >= limit && (
        <button
          onClick={() => {
            // Could open a modal or navigate to search results
          }}
          className="mt-4 text-sm font-medium text-fed-blue dark:text-blue-400 hover:underline"
        >
          View more related bills
        </button>
      )}
    </div>
  );
}
