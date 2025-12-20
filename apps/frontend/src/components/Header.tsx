'use client';

import Link from 'next/link';
import { ReactNode } from 'react';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';

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
    <header
      className={`bg-fed-blue dark:bg-gray-800 text-white py-6 ${className}`}
      data-testid="header"
    >
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between">
          {/* Left side - Title and navigation */}
          <div className="flex-1">
            {showBackLink && (
              <Link
                href={backLinkHref}
                className="text-blue-100 hover:text-white mb-2 inline-block text-sm"
                data-testid="header-back-link"
              >
                {backLinkText}
              </Link>
            )}

            <div className="flex items-center gap-3">
              {!showBackLink && (
                <Link href="/" className="flex items-center gap-3 group">
                  {/* Logo */}
                  <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center group-hover:bg-white/20 transition-colors">
                    <svg
                      className="w-6 h-6"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                      />
                    </svg>
                  </div>
                  <div>
                    <h1 className="text-xl sm:text-2xl font-bold">{title}</h1>
                    {subtitle && (
                      <p className="text-blue-100 text-sm hidden sm:block">
                        {subtitle}
                      </p>
                    )}
                  </div>
                </Link>
              )}

              {showBackLink && (
                <h1 className="text-lg sm:text-xl font-bold truncate max-w-md">
                  {title}
                </h1>
              )}
            </div>
          </div>

          {/* Right side - Theme toggle and User menu */}
          <div className="flex items-center gap-4">
            <ThemeToggle className="hidden sm:flex" />
            <UserMenu />
          </div>
        </div>

        {children}
      </div>
    </header>
  );
}
