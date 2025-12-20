'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { fetchBillDetail, type BillDetail } from '@/lib/api';
import {
  Header,
  BillDetailView,
  BillDetailSkeleton,
  ErrorAlert,
  Container,
  FeedbackButtons,
  BookmarkButton,
  TrackBillButton,
  ShareButton,
  SponsorInfo,
  BillTimeline,
  RelatedBills,
  CivicEngagement,
  Comments,
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

  const congress = parseInt(params.congress);
  const billType = params.billType;
  const number = parseInt(params.number);
  const billIdentifier = `${billType.toUpperCase()}-${number}`;

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Header showBackLink title="Loading..." subtitle="" />
        <main>
          <Container className="py-8">
            <BillDetailSkeleton />
          </Container>
        </main>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        <Header />
        <Container className="py-8">
          <ErrorAlert
            message={error || 'Bill not found'}
            onRetry={loadBillDetail}
            className="mb-4"
          />
          <Link href="/" className="link inline-block">
            ← Back to all bills
          </Link>
        </Container>
      </div>
    );
  }

  const { bill, explanation } = data;

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <Header
        showBackLink
        title={`${bill.bill_type.toUpperCase()}-${bill.number} (Congress ${bill.congress})`}
        subtitle=""
      />

      <main>
        <Container className="py-8">
          {/* Action bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
            <div className="flex items-center gap-3">
              <BookmarkButton
                billId={bill.congress + '-' + bill.bill_type + '-' + bill.number}
                congress={congress}
                billType={billType}
                number={number}
                size="md"
                showLabel
              />
              <TrackBillButton
                billId={bill.congress + '-' + bill.bill_type + '-' + bill.number}
                congress={congress}
                billType={billType}
                number={number}
                variant="button"
                size="md"
              />
            </div>
            <ShareButton
              title={`${billIdentifier}: ${bill.title}`}
              description={bill.summary || bill.title}
            />
          </div>

          <div className="grid lg:grid-cols-3 gap-8">
            {/* Main content - 2 columns */}
            <div className="lg:col-span-2 space-y-8">
              {/* Bill Details */}
              <BillDetailView bill={bill} explanation={explanation} />

              {/* Feedback on explanation */}
              {explanation && (
                <div className="card">
                  <FeedbackButtons
                    explanationId={`${congress}-${billType}-${number}-explanation`}
                    billId={`${congress}-${billType}-${number}`}
                  />
                </div>
              )}

              {/* Bill Timeline */}
              <div className="card">
                <BillTimeline
                  billId={`${congress}-${billType}-${number}`}
                  congress={congress}
                  billType={billType}
                  number={number}
                  introducedDate={(bill as any).introduced_date}
                  latestActionDate={(bill as any).latest_action_date}
                  status={bill.status}
                  publicLawNumber={bill.public_law_number}
                />
              </div>

              {/* Civic Engagement */}
              <CivicEngagement
                billTitle={bill.title}
                billIdentifier={billIdentifier}
              />

              {/* Comments/Discussion */}
              <Comments
                billId={`${congress}-${billType}-${number}`}
                congress={congress}
                billType={billType}
                number={number}
              />
            </div>

            {/* Sidebar - 1 column */}
            <div className="space-y-6">
              {/* Sponsor Info */}
              <SponsorInfo
                sponsor={(bill as any).sponsor}
                cosponsorsCount={(bill as any).cosponsors_count}
              />

              {/* Related Bills */}
              <RelatedBills
                billId={`${congress}-${billType}-${number}`}
                congress={congress}
                billType={billType}
                number={number}
                limit={5}
              />

              {/* External Links */}
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
                  External Links
                </h3>
                <div className="space-y-3">
                  <a
                    href={`https://www.congress.gov/bill/${congress}th-congress/${billType.replace('res', '-resolution').replace('j', 'joint-')}/${number}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-fed-blue dark:text-blue-400 hover:underline"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    View on Congress.gov
                  </a>
                  <a
                    href={`https://www.govtrack.us/congress/bills/${congress}/${billType}${number}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-sm text-fed-blue dark:text-blue-400 hover:underline"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    View on GovTrack
                  </a>
                </div>
              </div>
            </div>
          </div>
        </Container>
      </main>

      {/* Footer */}
      <footer className="bg-gray-100 dark:bg-gray-800 py-8 mt-12">
        <Container>
          <div className="text-center text-sm text-gray-600 dark:text-gray-400">
            <p>
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
            <p className="mt-2">
              AI explanations are generated for educational purposes and may not be fully accurate.
            </p>
          </div>
        </Container>
      </footer>
    </div>
  );
}
