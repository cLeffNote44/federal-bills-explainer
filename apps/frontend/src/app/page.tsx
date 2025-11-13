'use client';

import { useState, useEffect } from 'react';
import dynamic from 'next/dynamic';
import { fetchBills, type Bill } from '@/lib/api';
import {
  Header,
  SearchBar,
  BillList,
  Pagination,
  LoadingSpinner,
  ErrorAlert,
  Container,
  type FilterValues,
} from '@/components';

// Lazy load heavy components for better initial page load
const FilterPanel = dynamic(
  () => import('@/components/FilterPanel'),
  {
    loading: () => <div className="animate-pulse bg-gray-200 h-96 rounded-lg"></div>,
    ssr: false, // Filter panel doesn't need SSR
  }
);

const ExportButton = dynamic(
  () => import('@/components/ExportButton'),
  {
    loading: () => <div className="animate-pulse bg-gray-200 h-10 w-32 rounded-md"></div>,
    ssr: false, // Export buttons don't need SSR
  }
);

export default function HomePage() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<FilterValues>({
    sortBy: 'date',
    sortOrder: 'desc',
  });

  useEffect(() => {
    loadBills();
  }, [page]);

  async function loadBills() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchBills({
        q: search,
        page,
        status: filters.status,
        congress: filters.congress,
        bill_type: filters.billType,
        date_from: filters.dateFrom,
        date_to: filters.dateTo,
        has_public_law: filters.hasPublicLaw,
        sort_by: filters.sortBy,
        sort_order: filters.sortOrder,
      });
      setBills(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bills');
    } finally {
      setLoading(false);
    }
  }

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setPage(1);
    loadBills();
  }

  function handlePageChange(newPage: number) {
    setPage(newPage);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function handleApplyFilters() {
    setPage(1);
    loadBills();
  }

  function handleResetFilters() {
    setFilters({
      sortBy: 'date',
      sortOrder: 'desc',
    });
    setPage(1);
    // Will trigger loadBills via useEffect
    setTimeout(loadBills, 0);
  }

  function buildExportUrl(format: 'csv' | 'json'): string {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const params = new URLSearchParams();

    if (search) params.set('q', search);
    if (filters.status) params.set('status', filters.status);
    if (filters.congress) params.set('congress', filters.congress);
    if (filters.billType) params.set('bill_type', filters.billType);
    if (filters.dateFrom) params.set('date_from', filters.dateFrom);
    if (filters.dateTo) params.set('date_to', filters.dateTo);
    if (filters.hasPublicLaw !== undefined) params.set('has_public_law', filters.hasPublicLaw.toString());

    return `${apiBase}/export/${format}?${params.toString()}`;
  }

  return (
    <div className="min-h-screen">
      <Header />

      <main>
        <Container className="py-8">
          <SearchBar
            value={search}
            onChange={setSearch}
            onSubmit={handleSearch}
            disabled={loading}
            className="mb-6"
          />

          {/* Toolbar with Filters Toggle and Export Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-fed-blue"
            >
              <svg
                className="mr-2 h-5 w-5 text-gray-500"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z"
                />
              </svg>
              {showFilters ? 'Hide Filters' : 'Show Filters'}
            </button>

            <div className="flex gap-2">
              <ExportButton
                apiUrl={buildExportUrl('csv')}
                filename={`federal_bills_${new Date().toISOString().split('T')[0]}.csv`}
                format="csv"
                disabled={loading}
              />
              <ExportButton
                apiUrl={buildExportUrl('json')}
                filename={`federal_bills_${new Date().toISOString().split('T')[0]}.json`}
                format="json"
                disabled={loading}
              />
            </div>
          </div>

          {/* Filter Panel */}
          {showFilters && (
            <FilterPanel
              values={filters}
              onChange={setFilters}
              onApply={handleApplyFilters}
              onReset={handleResetFilters}
              className="mb-8"
            />
          )}

          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              className="mb-8"
            />
          )}

          {loading ? (
            <LoadingSpinner text="Loading bills..." />
          ) : (
            <>
              <BillList
                bills={bills}
                emptyMessage={
                  search
                    ? `No bills found matching "${search}"`
                    : 'No bills available'
                }
              />

              {bills.length > 0 && (
                <Pagination
                  currentPage={page}
                  onPageChange={handlePageChange}
                  hasNextPage={bills.length > 0}
                  disabled={loading}
                  className="mt-8"
                />
              )}
            </>
          )}
        </Container>
      </main>
    </div>
  );
}
