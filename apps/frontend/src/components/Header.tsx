import Link from 'next/link';
import { ReactNode } from 'react';
import MobileNav from './MobileNav';

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
    <header className={`bg-fed-blue text-white py-6 md:py-8 ${className}`} data-testid="header">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between mb-4 md:mb-0">
          <div className="flex-1">
            {showBackLink && (
              <Link
                href={backLinkHref}
                className="text-blue-100 hover:text-white mb-2 inline-block text-sm md:text-base"
                data-testid="header-back-link"
              >
                {backLinkText}
              </Link>
            )}

            <h1 className="text-2xl md:text-3xl font-bold">{title}</h1>

            {subtitle && (
              <p className="mt-1 md:mt-2 text-sm md:text-base text-blue-100">{subtitle}</p>
            )}
          </div>

          {/* Mobile Navigation */}
          <MobileNav />
        </div>

        {children}
      </div>
    </header>
  );
}
