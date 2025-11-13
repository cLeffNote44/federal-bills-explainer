import Link from 'next/link';
import { ReactNode } from 'react';

interface HeaderProps {
  title?: string;
  subtitle?: string;
  showBackLink?: boolean;
  backLinkText?: string;
  backLinkHref?: string;
  children?: ReactNode;
  className?: string;
}

export default function Header({
  title = 'Federal Bills Explainer',
  subtitle = 'Understanding US legislation made simple',
  showBackLink = false,
  backLinkText = '← Back to all bills',
  backLinkHref = '/',
  children,
  className = '',
}: HeaderProps) {
  return (
    <header className={`bg-fed-blue text-white py-8 ${className}`} data-testid="header">
      <div className="container mx-auto px-4">
        {showBackLink && (
          <Link
            href={backLinkHref}
            className="text-blue-100 hover:text-white mb-2 inline-block"
            data-testid="header-back-link"
          >
            {backLinkText}
          </Link>
        )}

        <h1 className="text-3xl font-bold">{title}</h1>

        {subtitle && (
          <p className="mt-2 text-blue-100">{subtitle}</p>
        )}

        {children}
      </div>
    </header>
  );
}
