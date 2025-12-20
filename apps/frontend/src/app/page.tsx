'use client';

import { useState, useEffect } from 'react';
import { fetchBills, type Bill } from '@/lib/api';
import {
  Header,
  SearchBar,
  BillList,
  BillListSkeleton,
  Pagination,
  ErrorAlert,
  Container,
  FilterPanel,
  ExportButton,
  TopicBrowser,
  type FilterValues,
} from '@/components';

export default function HomePage() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null);
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
    setSelectedTopic(null);
    setPage(1);
    setTimeout(loadBills, 0);
  }

  function handleTopicSelect(topic: string | null) {
    setSelectedTopic(topic);
    // In a real implementation, this would filter by topic
    setPage(1);
    loadBills();
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
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header />

      <main>
        <Container className="py-8">
          {/* Search Bar */}
          <SearchBar
            value={search}
            onChange={setSearch}
            onSubmit={handleSearch}
            disabled={loading}
            className="mb-6"
          />

          {/* Topic Browser */}
          <div className="mb-6">
            <TopicBrowser
              selectedTopic={selectedTopic || undefined}
              onSelectTopic={handleTopicSelect}
              variant="chips"
            />
          </div>

          {/* Toolbar with Filters Toggle and Export Buttons */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowFilters(!showFilters)}
                className="inline-flex items-center px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-fed-blue transition-colors"
              >
                <svg
                  className="mr-2 h-5 w-5 text-gray-500 dark:text-gray-400"
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

              {/* Active filters indicator */}
              {(filters.status || filters.congress || filters.billType || filters.dateFrom || filters.dateTo || selectedTopic) && (
                <span className="text-sm text-fed-blue dark:text-blue-400">
                  Filters active
                </span>
              )}
            </div>

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

          {/* Error Alert */}
          {error && (
            <ErrorAlert
              message={error}
              onDismiss={() => setError(null)}
              onRetry={loadBills}
              className="mb-8"
            />
          )}

          {/* Bills List or Skeleton */}
          {loading ? (
            <BillListSkeleton count={6} />
          ) : (
            <>
              <BillList
                bills={bills}
                emptyMessage={
                  search
                    ? `No bills found matching "${search}"`
                    : selectedTopic
                    ? `No bills found in topic "${selectedTopic}"`
                    : 'No bills available'
                }
              />

              {bills.length > 0 && (
                <Pagination
                  currentPage={page}
                  onPageChange={handlePageChange}
                  hasNextPage={bills.length >= 20}
                  disabled={loading}
                  className="mt-8"
                />
              )}
            </>
          )}
        </Container>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 dark:bg-gray-800 py-8 mt-12">
        <Container>
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>Federal Bills Explainer</p>
              <p className="mt-1">
                Data sourced from{' '}
                <a
                  href="https://www.congress.gov"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-fed-blue dark:text-blue-400 hover:underline"
                >
                  Congress.gov
                </a>
              </p>
            </div>
            <div className="flex gap-4 text-sm">
              <a href="/about" className="text-gray-600 dark:text-gray-400 hover:text-fed-blue dark:hover:text-blue-400">
                About
              </a>
              <a href="/privacy" className="text-gray-600 dark:text-gray-400 hover:text-fed-blue dark:hover:text-blue-400">
                Privacy
              </a>
              <a href="/terms" className="text-gray-600 dark:text-gray-400 hover:text-fed-blue dark:hover:text-blue-400">
                Terms
              </a>
            </div>
          </div>
        </Container>
      </footer>
    </div>
  );
}
