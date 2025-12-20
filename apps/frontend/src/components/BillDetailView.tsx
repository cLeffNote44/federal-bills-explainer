import { type Bill } from '@/lib/api';

interface BillDetailViewProps {
  bill: Bill;
  explanation?: string;
  className?: string;
}

export default function BillDetailView({ bill, explanation, className = '' }: BillDetailViewProps) {
  return (
    <div className={className} data-testid="bill-detail-view">
      {/* Official Title */}
      <div className="card mb-8">
        <h2 className="text-2xl font-semibold mb-4">Official Title</h2>
        <p className="text-gray-700">{bill.title}</p>
      </div>

      {/* Public Law Status */}
      {bill.public_law_number && (
        <div className="card mb-8 border-green-200 bg-green-50">
          <div className="flex items-center">
            <svg
              className="h-5 w-5 text-green-600 mr-2"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
            >
              <path
                fillRule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clipRule="evenodd"
              />
            </svg>
            <p className="text-green-700 font-semibold">
              Became Law: Public Law {bill.public_law_number}
            </p>
          </div>
        </div>
      )}

      {/* Official Summary */}
      {bill.summary && (
        <div className="card mb-8">
          <h2 className="text-2xl font-semibold mb-4">Official Summary</h2>
          <p className="text-gray-700 whitespace-pre-wrap">{bill.summary}</p>
        </div>
      )}

      {/* Plain Language Explanation */}
      {explanation && (
        <div className="card mb-8 border-blue-200 bg-blue-50">
          <div className="flex items-start">
            <svg
              className="h-6 w-6 text-fed-blue mt-1 mr-3 flex-shrink-0"
              xmlns="http://www.w3.org/2000/svg"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            <div className="flex-1">
              <h2 className="text-2xl font-semibold mb-4 text-fed-blue">
                Plain Language Explanation
              </h2>
              <p className="text-gray-700 whitespace-pre-wrap">{explanation}</p>
            </div>
          </div>
        </div>
      )}

      {/* Bill Information */}
      <div className="grid md:grid-cols-2 gap-6">
        {bill.status && (
          <div className="card">
            <h3 className="text-lg font-semibold mb-2 text-gray-700">Status</h3>
            <p className="text-gray-600 capitalize">{bill.status}</p>
          </div>
        )}

        <div className="card">
          <h3 className="text-lg font-semibold mb-2 text-gray-700">Bill Identifier</h3>
          <p className="text-gray-600">
            {bill.bill_type.toUpperCase()}-{bill.number}
            <span className="text-sm text-gray-500"> (Congress {bill.congress})</span>
          </p>
        </div>
      </div>
    </div>
  );
}
