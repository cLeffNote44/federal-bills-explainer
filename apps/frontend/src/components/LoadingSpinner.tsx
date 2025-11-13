interface LoadingSpinnerProps {
  text?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}

export default function LoadingSpinner({
  text = 'Loading...',
  size = 'md',
  className = '',
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-8 h-8',
    lg: 'w-12 h-12',
  };

  return (
    <div
      className={`flex flex-col items-center justify-center py-12 ${className}`}
      data-testid="loading-spinner"
      role="status"
      aria-live="polite"
    >
      <div className={`animate-spin rounded-full border-b-2 border-fed-blue ${sizeClasses[size]}`}></div>
      {text && (
        <p className="mt-4 text-gray-500">{text}</p>
      )}
    </div>
  );
}
