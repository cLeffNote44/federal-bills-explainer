'use client';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  animation?: 'pulse' | 'wave' | 'none';
}

export function Skeleton({
  className = '',
  variant = 'rectangular',
  width,
  height,
  animation = 'pulse',
}: SkeletonProps) {
  const baseClasses = 'bg-gray-200 dark:bg-gray-700';

  const animationClasses = {
    pulse: 'animate-pulse',
    wave: 'animate-shimmer bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200 dark:from-gray-700 dark:via-gray-600 dark:to-gray-700 bg-[length:200%_100%]',
    none: '',
  };

  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style = {
    width: typeof width === 'number' ? `${width}px` : width,
    height: typeof height === 'number' ? `${height}px` : height,
  };

  return (
    <div
      className={`${baseClasses} ${animationClasses[animation]} ${variantClasses[variant]} ${className}`}
      style={style}
      aria-hidden="true"
    />
  );
}

// Pre-built skeleton components for common use cases

export function BillCardSkeleton() {
  return (
    <div className="card" data-testid="bill-card-skeleton">
      <Skeleton className="h-6 w-24 mb-2" />
      <Skeleton className="h-4 w-20 mb-4" variant="text" />
      <Skeleton className="h-4 w-full mb-2" variant="text" />
      <Skeleton className="h-4 w-3/4 mb-4" variant="text" />
      <Skeleton className="h-4 w-1/2 mb-4" variant="text" />
      <Skeleton className="h-4 w-28" variant="text" />
    </div>
  );
}

export function BillListSkeleton({ count = 6 }: { count?: number }) {
  return (
    <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
      {Array.from({ length: count }).map((_, i) => (
        <BillCardSkeleton key={i} />
      ))}
    </div>
  );
}

export function BillDetailSkeleton() {
  return (
    <div data-testid="bill-detail-skeleton">
      {/* Title Section */}
      <div className="card mb-8">
        <Skeleton className="h-8 w-48 mb-4" />
        <Skeleton className="h-4 w-full mb-2" variant="text" />
        <Skeleton className="h-4 w-3/4" variant="text" />
      </div>

      {/* Summary Section */}
      <div className="card mb-8">
        <Skeleton className="h-8 w-40 mb-4" />
        <Skeleton className="h-4 w-full mb-2" variant="text" />
        <Skeleton className="h-4 w-full mb-2" variant="text" />
        <Skeleton className="h-4 w-2/3" variant="text" />
      </div>

      {/* Explanation Section */}
      <div className="card mb-8 border-blue-200 bg-blue-50 dark:bg-blue-900/20 dark:border-blue-800">
        <div className="flex items-start">
          <Skeleton className="h-6 w-6 mr-3" variant="circular" />
          <div className="flex-1">
            <Skeleton className="h-8 w-64 mb-4" />
            <Skeleton className="h-4 w-full mb-2" variant="text" />
            <Skeleton className="h-4 w-full mb-2" variant="text" />
            <Skeleton className="h-4 w-full mb-2" variant="text" />
            <Skeleton className="h-4 w-1/2" variant="text" />
          </div>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid md:grid-cols-2 gap-6">
        <div className="card">
          <Skeleton className="h-5 w-16 mb-2" />
          <Skeleton className="h-4 w-32" variant="text" />
        </div>
        <div className="card">
          <Skeleton className="h-5 w-24 mb-2" />
          <Skeleton className="h-4 w-40" variant="text" />
        </div>
      </div>
    </div>
  );
}

export function SearchResultsSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-white dark:bg-gray-800 rounded-lg">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 flex-1" variant="text" />
        </div>
      ))}
    </div>
  );
}

export function TimelineSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex gap-4">
          <div className="flex flex-col items-center">
            <Skeleton className="h-4 w-4" variant="circular" />
            {i < count - 1 && <Skeleton className="w-0.5 h-16 mt-2" />}
          </div>
          <div className="flex-1 pb-4">
            <Skeleton className="h-4 w-24 mb-2" variant="text" />
            <Skeleton className="h-4 w-full" variant="text" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function CommentSkeleton() {
  return (
    <div className="flex gap-3 p-4 border-b border-gray-200 dark:border-gray-700">
      <Skeleton className="h-10 w-10 flex-shrink-0" variant="circular" />
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-2">
          <Skeleton className="h-4 w-24" variant="text" />
          <Skeleton className="h-3 w-16" variant="text" />
        </div>
        <Skeleton className="h-4 w-full mb-1" variant="text" />
        <Skeleton className="h-4 w-2/3" variant="text" />
      </div>
    </div>
  );
}

export function CommentsSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div>
      {Array.from({ length: count }).map((_, i) => (
        <CommentSkeleton key={i} />
      ))}
    </div>
  );
}

export default Skeleton;
