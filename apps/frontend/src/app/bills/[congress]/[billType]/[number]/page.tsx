'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchBillDetail, type BillDetail } from '@/lib/api';
import {
  Header,
  BillDetailView,
  LoadingSpinner,
  ErrorAlert,
  Container,
} from '@/components';

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
      setError(null);
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
        <LoadingSpinner text="Loading bill details..." />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen">
        <Header />
        <Container className="py-8">
          <ErrorAlert message={error || 'Bill not found'} className="mb-4" />
          <Link href="/" className="text-fed-blue hover:underline inline-block">
            ← Back to all bills
          </Link>
        </Container>
      </div>
    );
  }

  const { bill, explanation } = data;

  return (
    <div className="min-h-screen">
      <Header
        showBackLink
        title={`${bill.bill_type.toUpperCase()}-${bill.number} (Congress ${bill.congress})`}
        subtitle=""
      />

      <main>
        <Container className="py-8">
          <BillDetailView bill={bill} explanation={explanation} />
        </Container>
      </main>
    </div>
  );
}
