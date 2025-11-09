'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchBillDetail, type BillDetail } from '@/lib/api';

interface PageProps {
  params: {
    congress: string;
    billType: string;
    number: string;
  };
}

export default function BillDetailPage({ params }: PageProps) {
  const [data, setData] = useState<BillDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadBillDetail();
  }, [params.congress, params.billType, params.number]);

  async function loadBillDetail() {
    try {
      setLoading(true);
      const billData = await fetchBillDetail(
        parseInt(params.congress),
        params.billType,
        parseInt(params.number)
      );
      setData(billData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load bill');
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-500">Loading bill details...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen">
        <div className="container mx-auto px-4 py-8">
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg">
            {error || 'Bill not found'}
          </div>
          <Link href="/" className="text-fed-blue hover:underline mt-4 inline-block">
            ← Back to all bills
          </Link>
        </div>
      </div>
    );
  }

  const { bill, explanation } = data;

  return (
    <div className="min-h-screen">
      <header className="bg-fed-blue text-white py-8">
        <div className="container mx-auto px-4">
          <Link href="/" className="text-blue-100 hover:text-white mb-2 inline-block">
            ← Back to all bills
          </Link>
          <h1 className="text-3xl font-bold">
            {bill.bill_type.toUpperCase()}-{bill.number} (Congress {bill.congress})
          </h1>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        <div className="card mb-8">
          <h2 className="text-2xl font-semibold mb-4">Official Title</h2>
          <p className="text-gray-700">{bill.title}</p>
        </div>

        {bill.public_law_number && (
          <div className="card mb-8 border-green-200 bg-green-50">
            <p className="text-green-700 font-semibold">
              ✓ Became Law: Public Law {bill.public_law_number}
            </p>
          </div>
        )}

        {bill.summary && (
          <div className="card mb-8">
            <h2 className="text-2xl font-semibold mb-4">Official Summary</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{bill.summary}</p>
          </div>
        )}

        {explanation && (
          <div className="card mb-8 border-blue-200 bg-blue-50">
            <h2 className="text-2xl font-semibold mb-4 text-fed-blue">Plain Language Explanation</h2>
            <p className="text-gray-700 whitespace-pre-wrap">{explanation}</p>
          </div>
        )}

        {bill.status && (
          <div className="card">
            <h2 className="text-xl font-semibold mb-2">Status</h2>
            <p className="text-gray-700">{bill.status}</p>
          </div>
        )}
      </main>
    </div>
  );
}
