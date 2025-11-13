'use client';

import { useEffect, useState } from 'react';

interface ErrorData {
  endpoint: string;
  status_code: number;
  timestamp: string;
  error_message?: string;
  user_agent?: string;
}

interface ErrorAnalyticsData {
  recent_errors: ErrorData[];
  error_by_endpoint: { [endpoint: string]: number };
  error_by_status: { [status: string]: number };
  timestamp: string;
}

interface ErrorAnalyticsProps {
  limit?: number;
  apiUrl?: string;
}

export default function ErrorAnalytics({
  limit = 20,
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}: ErrorAnalyticsProps) {
  const [data, setData] = useState<ErrorAnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState<'recent' | 'by-endpoint' | 'by-status'>('recent');

  useEffect(() => {
    fetchErrors();
    const interval = setInterval(fetchErrors, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, [limit]);

  const fetchErrors = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/analytics/errors?limit=${limit}`);
      if (!res.ok) throw new Error('Failed to fetch error analytics');
      const errorData = await res.json();
      setData(errorData);
      setError(null);
    } catch (err) {
      console.error('Error fetching error analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch error analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-red-600">{error}</div>
        <button
          onClick={fetchErrors}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data) {
    return null;
  }

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return timestamp;
    }
  };

  const getStatusColor = (status: number) => {
    if (status >= 500) return 'text-red-700 bg-red-100';
    if (status >= 400) return 'text-orange-700 bg-orange-100';
    return 'text-gray-700 bg-gray-100';
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Error Analytics</h2>
        <button
          onClick={fetchErrors}
          className="text-sm text-fed-blue hover:text-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Tabs */}
      <div className="flex space-x-4 mb-6 border-b border-gray-200">
        <button
          onClick={() => setSelectedTab('recent')}
          className={`pb-2 px-1 font-medium transition-colors ${
            selectedTab === 'recent'
              ? 'text-fed-blue border-b-2 border-fed-blue'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Recent Errors ({data.recent_errors.length})
        </button>
        <button
          onClick={() => setSelectedTab('by-endpoint')}
          className={`pb-2 px-1 font-medium transition-colors ${
            selectedTab === 'by-endpoint'
              ? 'text-fed-blue border-b-2 border-fed-blue'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          By Endpoint
        </button>
        <button
          onClick={() => setSelectedTab('by-status')}
          className={`pb-2 px-1 font-medium transition-colors ${
            selectedTab === 'by-status'
              ? 'text-fed-blue border-b-2 border-fed-blue'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          By Status Code
        </button>
      </div>

      {/* Tab Content */}
      {selectedTab === 'recent' && (
        <div className="space-y-3">
          {data.recent_errors.length === 0 ? (
            <div className="text-center py-8 text-gray-600">
              No recent errors - great job! 🎉
            </div>
          ) : (
            data.recent_errors.map((error, idx) => (
              <div
                key={idx}
                className="border border-gray-200 rounded-lg p-4 hover:border-red-300 transition-colors"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex-1">
                    <div className="font-mono text-sm text-gray-700 mb-1">
                      {error.endpoint}
                    </div>
                    {error.error_message && (
                      <div className="text-sm text-red-600 mb-1">{error.error_message}</div>
                    )}
                    <div className="text-xs text-gray-500">{formatTime(error.timestamp)}</div>
                  </div>
                  <span
                    className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(
                      error.status_code
                    )}`}
                  >
                    {error.status_code}
                  </span>
                </div>
                {error.user_agent && (
                  <div className="text-xs text-gray-500 truncate mt-2 pt-2 border-t border-gray-100">
                    UA: {error.user_agent}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}

      {selectedTab === 'by-endpoint' && (
        <div className="space-y-2">
          {Object.entries(data.error_by_endpoint)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 15)
            .map(([endpoint, count]) => (
              <div key={endpoint} className="flex items-center justify-between py-2 border-b border-gray-100">
                <div className="font-mono text-sm text-gray-700 flex-1 truncate">{endpoint}</div>
                <div className="ml-4 text-sm font-semibold text-red-600">{count} errors</div>
              </div>
            ))}
          {Object.keys(data.error_by_endpoint).length === 0 && (
            <div className="text-center py-8 text-gray-600">No errors to display</div>
          )}
        </div>
      )}

      {selectedTab === 'by-status' && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(data.error_by_status)
            .sort(([, a], [, b]) => b - a)
            .map(([status, count]) => (
              <div
                key={status}
                className={`rounded-lg p-4 ${getStatusColor(parseInt(status))} border-2`}
              >
                <div className="text-2xl font-bold mb-1">{status}</div>
                <div className="text-sm font-medium">{count} occurrences</div>
              </div>
            ))}
          {Object.keys(data.error_by_status).length === 0 && (
            <div className="col-span-2 text-center py-8 text-gray-600">No errors to display</div>
          )}
        </div>
      )}
    </div>
  );
}
