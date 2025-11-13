'use client';

import { useState, useEffect } from 'react';
import { fetchBills, type Bill } from '@/lib/api';
import {
  Header,
  SearchBar,
  BillList,
  Pagination,
  LoadingSpinner,
  ErrorAlert,
  Container,
} from '@/components';

export default function HomePage() {
  const [bills, setBills] = useState<Bill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);

  useEffect(() => {
    loadBills();
  }, [page]);

  async function loadBills() {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchBills({ q: search, page });
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
            className="mb-8"
          />

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
