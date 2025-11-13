'use client';

import { useEffect, useState } from 'react';

interface TrendsData {
  hourly_totals: { [hour: string]: number };
  detailed_trends: { [hour: string]: { [endpoint: string]: number } };
  hours: number;
  timestamp: string;
}

interface AnalyticsTrendsChartProps {
  hours?: number;
  apiUrl?: string;
}

export default function AnalyticsTrendsChart({
  hours = 24,
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
}: AnalyticsTrendsChartProps) {
  const [data, setData] = useState<TrendsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTrends();
    const interval = setInterval(fetchTrends, 60000); // Refresh every minute
    return () => clearInterval(interval);
  }, [hours]);

  const fetchTrends = async () => {
    try {
      setLoading(true);
      const res = await fetch(`${apiUrl}/analytics/trends?hours=${hours}`);
      if (!res.ok) throw new Error('Failed to fetch trends');
      const trendsData = await res.json();
      setData(trendsData);
      setError(null);
    } catch (err) {
      console.error('Error fetching trends:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch trends');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !data) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-red-600">{error}</div>
        <button
          onClick={fetchTrends}
          className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!data || Object.keys(data.hourly_totals).length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Request Trends</h2>
        <p className="text-gray-600">No trend data available</p>
      </div>
    );
  }

  // Sort hours and get values
  const sortedHours = Object.keys(data.hourly_totals).sort();
  const values = sortedHours.map(hour => data.hourly_totals[hour]);
  const maxValue = Math.max(...values, 1);

  // Format hour labels
  const formatHour = (hour: string) => {
    try {
      const date = new Date(hour);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return hour;
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold">Request Trends</h2>
        <div className="text-sm text-gray-600">
          Last {hours} hours
        </div>
      </div>

      {/* Bar Chart */}
      <div className="relative h-64 flex items-end justify-between space-x-1">
        {sortedHours.map((hour, idx) => {
          const value = data.hourly_totals[hour];
          const height = (value / maxValue) * 100;
          return (
            <div key={idx} className="flex-1 flex flex-col items-center group">
              <div className="relative w-full">
                {/* Tooltip */}
                <div className="absolute bottom-full mb-2 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs rounded py-1 px-2 opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {formatHour(hour)}
                  <br />
                  {value.toLocaleString()} requests
                </div>
                {/* Bar */}
                <div
                  className="w-full bg-fed-blue rounded-t hover:bg-blue-700 transition-colors cursor-pointer"
                  style={{ height: `${Math.max(height, 2)}%` }}
                ></div>
              </div>
            </div>
          );
        })}
      </div>

      {/* X-axis labels (show every 4th hour) */}
      <div className="flex justify-between mt-2 text-xs text-gray-600">
        {sortedHours.map((hour, idx) => {
          if (sortedHours.length <= 12 || idx % 4 === 0) {
            return (
              <div key={idx} className="flex-1 text-center">
                {formatHour(hour)}
              </div>
            );
          }
          return <div key={idx} className="flex-1"></div>;
        })}
      </div>

      {/* Summary Stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 grid grid-cols-3 gap-4">
        <div>
          <div className="text-sm text-gray-600">Total</div>
          <div className="text-lg font-semibold text-gray-900">
            {values.reduce((a, b) => a + b, 0).toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-600">Average</div>
          <div className="text-lg font-semibold text-gray-900">
            {Math.round(values.reduce((a, b) => a + b, 0) / values.length).toLocaleString()}
          </div>
        </div>
        <div>
          <div className="text-sm text-gray-600">Peak</div>
          <div className="text-lg font-semibold text-gray-900">
            {maxValue.toLocaleString()}
          </div>
        </div>
      </div>
    </div>
  );
}
