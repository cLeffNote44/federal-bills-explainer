import { type Bill } from '@/lib/api';
import BillCard from './BillCard';

interface BillListProps {
  bills: Bill[];
  emptyMessage?: string;
  className?: string;
}

export default function BillList({
  bills,
  emptyMessage = 'No bills found',
  className = '',
}: BillListProps) {
  if (bills.length === 0) {
    return (
      <div
        className={`text-center py-12 text-gray-500 ${className}`}
        data-testid="bill-list-empty"
      >
        {emptyMessage}
      </div>
    );
  }

  return (
    <div
      className={`grid gap-6 md:grid-cols-2 lg:grid-cols-3 ${className}`}
      data-testid="bill-list"
    >
      {bills.map((bill) => (
        <BillCard
          key={`${bill.congress}-${bill.bill_type}-${bill.number}`}
          bill={bill}
        />
      ))}
    </div>
  );
}
