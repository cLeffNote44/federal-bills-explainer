'use client';

interface PaginationProps {
  currentPage: number;
  onPageChange: (page: number) => void;
  hasNextPage: boolean;
  disabled?: boolean;
  className?: string;
}

export default function Pagination({
  currentPage,
  onPageChange,
  hasNextPage,
  disabled = false,
  className = '',
}: PaginationProps) {
  const canGoPrevious = currentPage > 1 && !disabled;
  const canGoNext = hasNextPage && !disabled;

  return (
    <div className={`flex justify-center gap-4 items-center ${className}`} data-testid="pagination">
      <button
        onClick={() => onPageChange(currentPage - 1)}
        disabled={!canGoPrevious}
        className="px-4 py-2 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        data-testid="pagination-previous"
      >
        Previous
      </button>

      <span className="px-4 py-2 text-gray-700" data-testid="pagination-current">
        Page {currentPage}
      </span>

      <button
        onClick={() => onPageChange(currentPage + 1)}
        disabled={!canGoNext}
        className="px-4 py-2 border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
        data-testid="pagination-next"
      >
        Next
      </button>
    </div>
  );
}
