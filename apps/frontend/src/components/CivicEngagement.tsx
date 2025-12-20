'use client';

import { useState } from 'react';
import { useAuth } from '@/contexts';

interface Representative {
  name: string;
  title: string;
  party: string;
  state: string;
  district?: number;
  phone?: string;
  website?: string;
  email?: string;
  photo_url?: string;
}

interface CivicEngagementProps {
  billTitle?: string;
  billIdentifier?: string;
  className?: string;
}

export default function CivicEngagement({
  billTitle,
  billIdentifier,
  className = '',
}: CivicEngagementProps) {
  const { user } = useAuth();
  const [zipCode, setZipCode] = useState(user?.zip_code || '');
  const [representatives, setRepresentatives] = useState<Representative[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showReps, setShowReps] = useState(false);

  const fetchRepresentatives = async () => {
    if (!zipCode || zipCode.length < 5) {
      setError('Please enter a valid 5-digit ZIP code');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // In a real app, this would call the Civic Information API
      // For demo purposes, we'll simulate the response
      await new Promise((resolve) => setTimeout(resolve, 500));

      // Simulated representatives data
      setRepresentatives([
        {
          name: 'Senator Jane Smith',
          title: 'U.S. Senator',
          party: 'D',
          state: zipCode.startsWith('9') ? 'CA' : zipCode.startsWith('1') ? 'NY' : 'TX',
          phone: '(202) 224-1234',
          website: 'https://www.senate.gov',
        },
        {
          name: 'Senator John Doe',
          title: 'U.S. Senator',
          party: 'R',
          state: zipCode.startsWith('9') ? 'CA' : zipCode.startsWith('1') ? 'NY' : 'TX',
          phone: '(202) 224-5678',
          website: 'https://www.senate.gov',
        },
        {
          name: 'Rep. Alex Johnson',
          title: 'U.S. Representative',
          party: 'D',
          state: zipCode.startsWith('9') ? 'CA' : zipCode.startsWith('1') ? 'NY' : 'TX',
          district: 12,
          phone: '(202) 225-1234',
          website: 'https://www.house.gov',
        },
      ]);
      setShowReps(true);
    } catch {
      setError('Unable to find representatives. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const getContactMessage = () => {
    if (billTitle && billIdentifier) {
      return `I am contacting you regarding ${billIdentifier}: "${billTitle}". I would like to express my views on this legislation.`;
    }
    return 'I am contacting you regarding federal legislation.';
  };

  return (
    <div className={`card ${className}`}>
      <div className="flex items-center gap-3 mb-4">
        <div className="p-2 bg-fed-blue/10 dark:bg-fed-blue/20 rounded-lg">
          <svg
            className="w-6 h-6 text-fed-blue dark:text-blue-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
            />
          </svg>
        </div>
        <div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Contact Your Representatives
          </h3>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Make your voice heard on this legislation
          </p>
        </div>
      </div>

      {!showReps ? (
        <div>
          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            Enter your ZIP code to find your representatives
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={zipCode}
              onChange={(e) => setZipCode(e.target.value.replace(/\D/g, '').slice(0, 5))}
              placeholder="12345"
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-fed-blue focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
              maxLength={5}
            />
            <button
              onClick={fetchRepresentatives}
              disabled={loading || zipCode.length < 5}
              className="px-4 py-2 bg-fed-blue text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
            >
              {loading ? 'Finding...' : 'Find'}
            </button>
          </div>
          {error && (
            <p className="mt-2 text-sm text-red-600 dark:text-red-400">{error}</p>
          )}
        </div>
      ) : (
        <div>
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm text-gray-500 dark:text-gray-400">
              Showing representatives for ZIP {zipCode}
            </span>
            <button
              onClick={() => {
                setShowReps(false);
                setRepresentatives([]);
              }}
              className="text-sm text-fed-blue dark:text-blue-400 hover:underline"
            >
              Change ZIP
            </button>
          </div>

          <div className="space-y-4">
            {representatives.map((rep, index) => (
              <div
                key={index}
                className="flex items-start gap-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
              >
                {/* Avatar */}
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center text-white font-bold ${
                    rep.party === 'D'
                      ? 'bg-blue-500'
                      : rep.party === 'R'
                      ? 'bg-red-500'
                      : 'bg-gray-500'
                  }`}
                >
                  {rep.name.split(' ').map((n) => n[0]).join('').slice(0, 2)}
                </div>

                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-900 dark:text-gray-100">
                      {rep.name}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-xs font-medium ${
                        rep.party === 'D'
                          ? 'bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300'
                          : rep.party === 'R'
                          ? 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'
                      }`}
                    >
                      {rep.party}
                    </span>
                  </div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    {rep.title} • {rep.state}
                    {rep.district && `-${rep.district}`}
                  </p>

                  <div className="mt-2 flex flex-wrap gap-2">
                    {rep.phone && (
                      <a
                        href={`tel:${rep.phone.replace(/\D/g, '')}`}
                        className="inline-flex items-center gap-1 text-sm text-fed-blue dark:text-blue-400 hover:underline"
                      >
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
                            d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
                          />
                        </svg>
                        {rep.phone}
                      </a>
                    )}
                    {rep.website && (
                      <a
                        href={rep.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-fed-blue dark:text-blue-400 hover:underline"
                      >
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
                        Website
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Call script */}
          <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <h4 className="text-sm font-semibold text-fed-blue dark:text-blue-400 mb-2">
              Sample Call Script
            </h4>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              "Hello, my name is [Your Name] and I'm a constituent from [Your City]. {getContactMessage()} Thank you for your time."
            </p>
          </div>

          {/* Voter registration link */}
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <a
              href="https://vote.gov"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 text-sm font-medium text-fed-blue dark:text-blue-400 hover:underline"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              Check your voter registration status
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
