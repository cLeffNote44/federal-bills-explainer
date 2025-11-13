import Link from 'next/link';
import { type Bill } from '@/lib/api';

interface BillCardProps {
  bill: Bill;
  className?: string;
}

export default function BillCard({ bill, className = '' }: BillCardProps) {
  return (
    <div
      className={`card ${className}`}
      data-testid="bill-card"
    >
      <h2 className="text-xl font-semibold mb-2">
        {bill.bill_type.toUpperCase()}-{bill.number}
      </h2>

      <p className="text-sm text-gray-500 mb-2">
        Congress {bill.congress}
      </p>

      <p className="text-gray-600 mb-4 line-clamp-3">
        {bill.title}
      </p>

      {bill.summary && (
        <p className="text-sm text-gray-500 mb-4 line-clamp-2">
          {bill.summary}
        </p>
      )}

      {bill.public_law_number && (
        <div className="mb-4">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            ✓ Public Law {bill.public_law_number}
          </span>
        </div>
      )}

      {bill.status && (
        <p className="text-sm text-gray-600 mb-4 capitalize">
          Status: {bill.status}
        </p>
      )}

      <Link
        href={`/bills/${bill.congress}/${bill.bill_type}/${bill.number}`}
        className="text-fed-blue hover:underline inline-flex items-center"
        data-testid="bill-card-link"
      >
        View Details →
      </Link>
    </div>
  );
}
