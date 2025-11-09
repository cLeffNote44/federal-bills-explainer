'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { fetchBills, type Bill } from '@/lib/api';

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

  return (
    <div className="min-h-screen">
      <header className="bg-fed-blue text-white py-8">
        <div className="container mx-auto px-4">
          <h1 className="text-3xl font-bold">Federal Bills Explainer</h1>
          <p className="mt-2 text-blue-100">Understanding US legislation made simple</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <form onSubmit={handleSearch} className="mb-8">
          <div className="flex gap-4 max-w-2xl">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search bills..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:border-fed-blue"
            />
            <button type="submit" className="btn-primary">
              Search
            </button>
          </div>
        </form>

        {loading && (
          <div className="text-center py-12">
            <div className="text-gray-500">Loading bills...</div>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-8">
            {error}
          </div>
        )}

        {!loading && !error && (
          <>
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {bills.map((bill) => (
                <div key={`${bill.congress}-${bill.bill_type}-${bill.number}`} className="card">
                  <h2 className="text-xl font-semibold mb-2">
                    {bill.bill_type.toUpperCase()}-{bill.number}
                  </h2>
                  <p className="text-gray-600 mb-4 line-clamp-3">{bill.title}</p>
                  {bill.public_law_number && (
                    <p className="text-sm text-green-600 mb-4">
                      ✓ Public Law {bill.public_law_number}
                    </p>
                  )}
                  <Link
                    href={`/bills/${bill.congress}/${bill.bill_type}/${bill.number}`}
                    className="text-fed-blue hover:underline"
                  >
                    View Details →
                  </Link>
                </div>
              ))}
            </div>

            <div className="mt-8 flex justify-center gap-4">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 border border-gray-300 rounded disabled:opacity-50"
              >
                Previous
              </button>
              <span className="px-4 py-2">Page {page}</span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={bills.length === 0}
                className="px-4 py-2 border border-gray-300 rounded disabled:opacity-50"
              >
                Next
              </button>
            </div>
          </>
        )}
      </main>
    </div>
  );
}
