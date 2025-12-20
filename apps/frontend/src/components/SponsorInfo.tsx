'use client';

import { useState } from 'react';

interface Sponsor {
  bioguide_id?: string;
  name: string;
  first_name?: string;
  last_name?: string;
  party?: string;
  state?: string;
  district?: number;
  title?: string; // Rep. or Sen.
  url?: string;
}

interface SponsorInfoProps {
  sponsor?: Sponsor | null;
  cosponsorsCount?: number;
  className?: string;
}

const partyColors: Record<string, { bg: string; text: string; border: string }> = {
  D: {
    bg: 'bg-blue-100 dark:bg-blue-900/30',
    text: 'text-blue-700 dark:text-blue-300',
    border: 'border-blue-200 dark:border-blue-800',
  },
  R: {
    bg: 'bg-red-100 dark:bg-red-900/30',
    text: 'text-red-700 dark:text-red-300',
    border: 'border-red-200 dark:border-red-800',
  },
  I: {
    bg: 'bg-purple-100 dark:bg-purple-900/30',
    text: 'text-purple-700 dark:text-purple-300',
    border: 'border-purple-200 dark:border-purple-800',
  },
  default: {
    bg: 'bg-gray-100 dark:bg-gray-800',
    text: 'text-gray-700 dark:text-gray-300',
    border: 'border-gray-200 dark:border-gray-700',
  },
};

function getPartyName(code?: string): string {
  const parties: Record<string, string> = {
    D: 'Democrat',
    R: 'Republican',
    I: 'Independent',
    L: 'Libertarian',
    G: 'Green',
  };
  return parties[code || ''] || code || 'Unknown';
}

function getPartyColor(code?: string) {
  return partyColors[code || ''] || partyColors.default;
}

export default function SponsorInfo({
  sponsor,
  cosponsorsCount,
  className = '',
}: SponsorInfoProps) {
  const [showDetails, setShowDetails] = useState(false);

  if (!sponsor) {
    return (
      <div className={`card ${className}`}>
        <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
          Sponsor
        </h3>
        <p className="text-gray-500 dark:text-gray-400 text-sm">
          Sponsor information not available
        </p>
      </div>
    );
  }

  const partyStyle = getPartyColor(sponsor.party);
  const displayName =
    sponsor.name ||
    `${sponsor.first_name || ''} ${sponsor.last_name || ''}`.trim() ||
    'Unknown';
  const title = sponsor.title || (sponsor.state ? 'Member' : '');

  return (
    <div className={`card ${className}`}>
      <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-4">
        Sponsor
      </h3>

      <div className="flex items-start gap-4">
        {/* Avatar/Initials */}
        <div
          className={`w-12 h-12 rounded-full flex items-center justify-center text-lg font-bold ${partyStyle.bg} ${partyStyle.text}`}
        >
          {sponsor.first_name?.[0] || sponsor.name?.[0] || '?'}
          {sponsor.last_name?.[0] || ''}
        </div>

        <div className="flex-1">
          {/* Name and Party */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-semibold text-gray-900 dark:text-gray-100">
              {title && `${title} `}
              {displayName}
            </span>
            {sponsor.party && (
              <span
                className={`px-2 py-0.5 rounded text-xs font-medium ${partyStyle.bg} ${partyStyle.text}`}
              >
                {sponsor.party}
              </span>
            )}
          </div>

          {/* Location */}
          {(sponsor.state || sponsor.district !== undefined) && (
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              {sponsor.state}
              {sponsor.district !== undefined && `-${sponsor.district}`}
            </p>
          )}

          {/* Details Toggle */}
          {(sponsor.bioguide_id || sponsor.url) && (
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-fed-blue dark:text-blue-400 hover:underline mt-2"
            >
              {showDetails ? 'Hide details' : 'Show details'}
            </button>
          )}

          {/* Expanded Details */}
          {showDetails && (
            <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700 space-y-2">
              {sponsor.party && (
                <p className="text-sm">
                  <span className="text-gray-500 dark:text-gray-400">Party:</span>{' '}
                  <span className="text-gray-700 dark:text-gray-300">
                    {getPartyName(sponsor.party)}
                  </span>
                </p>
              )}
              {sponsor.bioguide_id && (
                <p className="text-sm">
                  <span className="text-gray-500 dark:text-gray-400">
                    Bioguide ID:
                  </span>{' '}
                  <span className="text-gray-700 dark:text-gray-300 font-mono">
                    {sponsor.bioguide_id}
                  </span>
                </p>
              )}
              {sponsor.url && (
                <a
                  href={sponsor.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-sm text-fed-blue dark:text-blue-400 hover:underline"
                >
                  View on Congress.gov
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
                </a>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Cosponsors Count */}
      {cosponsorsCount !== undefined && cosponsorsCount > 0 && (
        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <svg
              className="w-5 h-5 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              <span className="font-semibold">{cosponsorsCount}</span> co-sponsor
              {cosponsorsCount !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
