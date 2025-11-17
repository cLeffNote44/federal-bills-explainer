'use client';

import { useEffect, useState } from 'react';

interface UserAgentData {
  categories: {
    mobile: number;
    desktop: number;
    bot: number;
    unknown: number;
  };
  browsers: { [browser: string]: number };
  raw_user_agents: { [ua: string]: number };
  timestamp: string;
}

interface UserAgentAnalyticsProps {
  apiUrl?: string;
}

export default function UserAgentAnalytics({
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}: UserAgentAnalyticsProps) {
  const [data, setData] = useState<UserAgentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchUserAgents();
    const interval = setInterval(fetchUserAgents, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, []);

  const fetchUserAgents = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/analytics/user-agents`);
      if (!res.ok) throw new Error('Failed to fetch user agent analytics');
      const uaData = await res.json();
      setData(uaData);
      setError(null);
    } catch (err) {
      console.error('Error fetching user agent analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch user agent analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/3 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-32 bg-gray-200 rounded"></div>
            <div className="h-32 bg-gray-200 rounded"></div>
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
          onClick={fetchUserAgents}
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

  const totalRequests = Object.values(data.categories).reduce((a, b) => a + b, 0);
  const getPercentage = (value: number): string => {
    if (totalRequests === 0) return '0.0';
    return ((value / totalRequests) * 100).toFixed(1);
  };

  const categoryColors = {
    mobile: 'bg-green-500',
    desktop: 'bg-blue-500',
    bot: 'bg-purple-500',
    unknown: 'bg-gray-400',
  };

  const categoryIcons = {
    mobile: '📱',
    desktop: '💻',
    bot: '🤖',
    unknown: '❓',
  };

  const browserColors: { [key: string]: string } = {
    Chrome: 'bg-yellow-500',
    Firefox: 'bg-orange-500',
    Safari: 'bg-blue-400',
    Edge: 'bg-green-600',
    Other: 'bg-gray-500',
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">User Agent Analytics</h2>
        <button
          onClick={fetchUserAgents}
          className="text-sm text-fed-blue hover:text-blue-700"
        >
          Refresh
        </button>
      </div>

      {/* Device Categories */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold mb-4">Device Types</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          {Object.entries(data.categories).map(([category, count]) => (
            <div key={category} className="bg-gray-50 rounded-lg p-4 text-center">
              <div className="text-3xl mb-2">
                {categoryIcons[category as keyof typeof categoryIcons]}
              </div>
              <div className="text-sm text-gray-600 mb-1 capitalize">{category}</div>
              <div className="text-2xl font-bold text-gray-900">{count.toLocaleString()}</div>
              <div className="text-xs text-gray-500 mt-1">{getPercentage(count)}%</div>
            </div>
          ))}
        </div>

        {/* Visual Bar */}
        <div className="flex rounded-lg overflow-hidden h-6">
          {Object.entries(data.categories).map(([category, count]) => {
            const width = getPercentage(count);
            if (parseFloat(width) === 0) return null;
            return (
              <div
                key={category}
                className={`${categoryColors[category as keyof typeof categoryColors]} flex items-center justify-center text-white text-xs font-semibold`}
                style={{ width: `${width}%` }}
                title={`${category}: ${count} (${width}%)`}
              >
                {parseFloat(width) > 10 ? `${width}%` : ''}
              </div>
            );
          })}
        </div>
      </div>

      {/* Browser Distribution */}
      <div>
        <h3 className="text-lg font-semibold mb-4">Browser Distribution</h3>
        <div className="space-y-3">
          {Object.entries(data.browsers)
            .sort(([, a], [, b]) => b - a)
            .map(([browser, count]) => {
              const percentage = getPercentage(count);
              return (
                <div key={browser} className="flex items-center">
                  <div className="w-24 text-sm font-medium text-gray-700">{browser}</div>
                  <div className="flex-1 mx-4">
                    <div className="w-full bg-gray-200 rounded-full h-4">
                      <div
                        className={`${browserColors[browser] || 'bg-gray-500'} rounded-full h-4 flex items-center justify-end pr-2`}
                        style={{ width: `${percentage}%` }}
                      >
                        {parseFloat(percentage) > 5 && (
                          <span className="text-white text-xs font-semibold">{percentage}%</span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="w-16 text-right text-sm text-gray-600">{count.toLocaleString()}</div>
                </div>
              );
            })}
          {Object.keys(data.browsers).length === 0 && (
            <div className="text-center py-8 text-gray-600">No browser data available</div>
          )}
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="text-sm text-gray-600">
          Total Unique User Agents: {Object.keys(data.raw_user_agents).length}
        </div>
      </div>
    </div>
  );
}
