'use client';

import { useState, useEffect } from 'react';
import { fetchBillDetail, type Bill, type BillDetail } from '@/lib/api';
import { BillDetailSkeleton } from './Skeleton';

interface BillComparisonProps {
  bills: Array<{ congress: number; billType: string; number: number }>;
  onRemoveBill?: (index: number) => void;
  className?: string;
}

interface ComparisonData {
  bill: Bill;
  explanation?: string;
  loading: boolean;
  error?: string;
}

export default function BillComparison({
  bills,
  onRemoveBill,
  className = '',
}: BillComparisonProps) {
  const [comparisonData, setComparisonData] = useState<ComparisonData[]>([]);

  useEffect(() => {
    const loadBillDetails = async () => {
      const initialData: ComparisonData[] = bills.map(() => ({
        bill: {} as Bill,
        loading: true,
      }));
      setComparisonData(initialData);

      const results = await Promise.all(
        bills.map(async (billRef, index) => {
          try {
            const data = await fetchBillDetail(
              billRef.congress,
              billRef.billType,
              billRef.number
            );
            return { ...data, loading: false };
          } catch (error) {
            return {
              bill: {} as Bill,
              loading: false,
              error: error instanceof Error ? error.message : 'Failed to load',
            };
          }
        })
      );

      setComparisonData(results);
    };

    if (bills.length > 0) {
      loadBillDetails();
    }
  }, [bills]);

  if (bills.length === 0) {
    return (
      <div className={`text-center py-12 ${className}`}>
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
            d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2"
          />
        </svg>
        <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-gray-100">
          No bills to compare
        </h3>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Add bills to compare them side by side
        </p>
      </div>
    );
  }

  const gridCols = bills.length === 2 ? 'md:grid-cols-2' : 'md:grid-cols-3';

  return (
    <div className={className}>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
          Bill Comparison
        </h2>
        <span className="text-sm text-gray-500 dark:text-gray-400">
          Comparing {bills.length} bills
        </span>
      </div>

      <div className={`grid gap-6 ${gridCols}`}>
        {comparisonData.map((data, index) => (
          <div
            key={`${bills[index].congress}-${bills[index].billType}-${bills[index].number}`}
            className="relative"
          >
            {/* Remove button */}
            {onRemoveBill && (
              <button
                onClick={() => onRemoveBill(index)}
                className="absolute -top-2 -right-2 z-10 p-1 bg-red-100 dark:bg-red-900 text-red-600 dark:text-red-300 rounded-full hover:bg-red-200 dark:hover:bg-red-800 transition-colors"
                aria-label="Remove from comparison"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            )}

            {data.loading ? (
              <BillDetailSkeleton />
            ) : data.error ? (
              <div className="card bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                <p className="text-red-600 dark:text-red-400">{data.error}</p>
              </div>
            ) : (
              <div className="card h-full">
                {/* Header */}
                <div className="border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
                  <span className="inline-block px-2 py-1 text-xs font-semibold bg-fed-blue text-white rounded mb-2">
                    {data.bill.bill_type.toUpperCase()}-{data.bill.number}
                  </span>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Congress {data.bill.congress}
                  </p>
                </div>

                {/* Title */}
                <div className="mb-4">
                  <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                    Title
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-4">
                    {data.bill.title}
                  </p>
                </div>

                {/* Status */}
                {data.bill.status && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Status
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {data.bill.status}
                    </p>
                  </div>
                )}

                {/* Public Law */}
                {data.bill.public_law_number && (
                  <div className="mb-4">
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 dark:bg-green-900 text-green-800 dark:text-green-200">
                      Public Law {data.bill.public_law_number}
                    </span>
                  </div>
                )}

                {/* Summary */}
                {data.bill.summary && (
                  <div className="mb-4">
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">
                      Summary
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-6">
                      {data.bill.summary}
                    </p>
                  </div>
                )}

                {/* Explanation */}
                {data.explanation && (
                  <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 mt-4">
                    <h3 className="text-sm font-semibold text-fed-blue dark:text-blue-400 mb-1">
                      Plain Language
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-6">
                      {data.explanation}
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Comparison highlights */}
      {comparisonData.every((d) => !d.loading && !d.error) && bills.length >= 2 && (
        <div className="mt-8 card bg-gray-50 dark:bg-gray-800">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            Key Differences
          </h3>
          <div className="space-y-3">
            <ComparisonRow
              label="Bill Type"
              values={comparisonData.map((d) => d.bill.bill_type?.toUpperCase() || 'N/A')}
            />
            <ComparisonRow
              label="Congress"
              values={comparisonData.map((d) => d.bill.congress?.toString() || 'N/A')}
            />
            <ComparisonRow
              label="Status"
              values={comparisonData.map((d) => d.bill.status || 'Unknown')}
            />
            <ComparisonRow
              label="Became Law"
              values={comparisonData.map((d) =>
                d.bill.public_law_number ? `Yes (${d.bill.public_law_number})` : 'No'
              )}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function ComparisonRow({ label, values }: { label: string; values: string[] }) {
  const allSame = values.every((v) => v === values[0]);

  return (
    <div className="flex items-start gap-4">
      <span className="text-sm font-medium text-gray-700 dark:text-gray-300 w-24 flex-shrink-0">
        {label}
      </span>
      <div className="flex flex-1 gap-4">
        {values.map((value, i) => (
          <span
            key={i}
            className={`flex-1 text-sm ${
              allSame
                ? 'text-gray-600 dark:text-gray-400'
                : 'text-fed-blue dark:text-blue-400 font-medium'
            }`}
          >
            {value}
          </span>
        ))}
      </div>
    </div>
  );
}
