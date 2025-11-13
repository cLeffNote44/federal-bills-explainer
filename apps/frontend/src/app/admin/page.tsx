'use client';

import { useEffect, useState } from 'react';
import { Container } from '@/components';

interface AnalyticsOverview {
  total_requests: number;
  avg_response_time: number;
  error_rate: number;
  total_errors: number;
  popular_endpoints: Array<{ endpoint: string; count: number }>;
  timestamp: string;
}

interface EndpointStats {
  [key: string]: {
    count: number;
    error_count: number;
    avg_response_time: number;
    p95_response_time: number;
    p99_response_time: number;
  };
}

interface PerformanceMetrics {
  overall_percentiles: {
    p50: number;
    p95: number;
    p99: number;
  };
  slowest_endpoints: Array<{
    endpoint: string;
    avg_response_time: number;
    p95_response_time: number;
    p99_response_time: number;
    count: number;
  }>;
  timestamp: string;
}

interface PopularBill {
  bill_id: string;
  views: number;
}

export default function AdminDashboard() {
  const [overview, setOverview] = useState<AnalyticsOverview | null>(null);
  const [performance, setPerformance] = useState<PerformanceMetrics | null>(null);
  const [popularBills, setPopularBills] = useState<PopularBill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<number>(24);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchAnalytics();
    // Refresh every 30 seconds
    const interval = setInterval(fetchAnalytics, 30000);
    return () => clearInterval(interval);
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch overview
      const overviewRes = await fetch(`${API_URL}/analytics/overview`);
      if (!overviewRes.ok) throw new Error('Failed to fetch overview');
      const overviewData = await overviewRes.json();
      setOverview(overviewData);

      // Fetch performance metrics
      const perfRes = await fetch(`${API_URL}/analytics/performance`);
      if (!perfRes.ok) throw new Error('Failed to fetch performance');
      const perfData = await perfRes.json();
      setPerformance(perfData);

      // Fetch popular bills
      const billsRes = await fetch(`${API_URL}/analytics/bills/popular?limit=10`);
      if (!billsRes.ok) throw new Error('Failed to fetch popular bills');
      const billsData = await billsRes.json();
      setPopularBills(billsData.popular_bills);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading && !overview) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-fed-blue mx-auto mb-4"></div>
          <p className="text-gray-600">Loading analytics...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Container>
        <div className="py-8">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h2 className="text-red-800 font-semibold mb-2">Error Loading Analytics</h2>
            <p className="text-red-600">{error}</p>
            <button
              onClick={fetchAnalytics}
              className="mt-4 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </Container>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Container>
        <div className="py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Analytics Dashboard</h1>
            <p className="text-gray-600">Monitor API usage and performance metrics</p>
            <div className="mt-4 flex items-center gap-4">
              <button
                onClick={fetchAnalytics}
                className="px-4 py-2 bg-fed-blue text-white rounded-lg hover:bg-blue-700 transition-colors"
                disabled={loading}
              >
                {loading ? 'Refreshing...' : 'Refresh Data'}
              </button>
              <span className="text-sm text-gray-500">
                Last updated: {overview ? new Date(overview.timestamp).toLocaleString() : 'N/A'}
              </span>
            </div>
          </div>

          {/* Overview Cards */}
          {overview && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              <MetricCard
                title="Total Requests"
                value={overview.total_requests.toLocaleString()}
                icon="📊"
                trend={null}
              />
              <MetricCard
                title="Avg Response Time"
                value={`${overview.avg_response_time.toFixed(0)}ms`}
                icon="⚡"
                trend={null}
              />
              <MetricCard
                title="Error Rate"
                value={`${overview.error_rate.toFixed(2)}%`}
                icon="⚠️"
                trend={null}
                isError={overview.error_rate > 5}
              />
              <MetricCard
                title="Total Errors"
                value={overview.total_errors.toLocaleString()}
                icon="❌"
                trend={null}
                isError={overview.total_errors > 0}
              />
            </div>
          )}

          {/* Performance Metrics */}
          {performance && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold mb-4">Response Time Percentiles</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                <div className="bg-blue-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">P50 (Median)</div>
                  <div className="text-2xl font-bold text-fed-blue">
                    {performance.overall_percentiles.p50.toFixed(0)}ms
                  </div>
                </div>
                <div className="bg-yellow-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">P95</div>
                  <div className="text-2xl font-bold text-yellow-700">
                    {performance.overall_percentiles.p95.toFixed(0)}ms
                  </div>
                </div>
                <div className="bg-red-50 rounded-lg p-4">
                  <div className="text-sm text-gray-600 mb-1">P99</div>
                  <div className="text-2xl font-bold text-red-700">
                    {performance.overall_percentiles.p99.toFixed(0)}ms
                  </div>
                </div>
              </div>

              <h3 className="text-lg font-semibold mb-3">Slowest Endpoints</h3>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 px-4 text-sm font-medium text-gray-600">Endpoint</th>
                      <th className="text-right py-2 px-4 text-sm font-medium text-gray-600">Avg</th>
                      <th className="text-right py-2 px-4 text-sm font-medium text-gray-600">P95</th>
                      <th className="text-right py-2 px-4 text-sm font-medium text-gray-600">P99</th>
                      <th className="text-right py-2 px-4 text-sm font-medium text-gray-600">Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {performance.slowest_endpoints.slice(0, 5).map((endpoint, idx) => (
                      <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-2 px-4 text-sm font-mono text-gray-700">
                          {endpoint.endpoint}
                        </td>
                        <td className="text-right py-2 px-4 text-sm text-gray-600">
                          {endpoint.avg_response_time.toFixed(0)}ms
                        </td>
                        <td className="text-right py-2 px-4 text-sm text-gray-600">
                          {endpoint.p95_response_time.toFixed(0)}ms
                        </td>
                        <td className="text-right py-2 px-4 text-sm text-gray-600">
                          {endpoint.p99_response_time.toFixed(0)}ms
                        </td>
                        <td className="text-right py-2 px-4 text-sm text-gray-600">
                          {endpoint.count.toLocaleString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Popular Endpoints */}
          {overview && overview.popular_endpoints.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6 mb-8">
              <h2 className="text-xl font-semibold mb-4">Popular Endpoints</h2>
              <div className="space-y-3">
                {overview.popular_endpoints.slice(0, 10).map((endpoint, idx) => (
                  <div key={idx} className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-mono text-sm text-gray-700">{endpoint.endpoint}</div>
                      <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                        <div
                          className="bg-fed-blue rounded-full h-2"
                          style={{
                            width: `${(endpoint.count / overview.popular_endpoints[0].count) * 100}%`,
                          }}
                        ></div>
                      </div>
                    </div>
                    <div className="ml-4 text-sm font-semibold text-gray-600">
                      {endpoint.count.toLocaleString()}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Popular Bills */}
          {popularBills.length > 0 && (
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-xl font-semibold mb-4">Most Viewed Bills</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {popularBills.map((bill, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                  >
                    <div>
                      <div className="font-semibold text-gray-900">{bill.bill_id}</div>
                      <div className="text-sm text-gray-600">{bill.views} views</div>
                    </div>
                    <div className="text-2xl">📄</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </Container>
    </div>
  );
}

interface MetricCardProps {
  title: string;
  value: string;
  icon: string;
  trend: number | null;
  isError?: boolean;
}

function MetricCard({ title, value, icon, trend, isError = false }: MetricCardProps) {
  return (
    <div className={`bg-white rounded-lg shadow-md p-6 ${isError ? 'border-2 border-red-300' : ''}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="text-sm font-medium text-gray-600">{title}</div>
        <div className="text-2xl">{icon}</div>
      </div>
      <div className={`text-3xl font-bold mb-1 ${isError ? 'text-red-600' : 'text-gray-900'}`}>
        {value}
      </div>
      {trend !== null && (
        <div className={`text-sm ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {trend > 0 ? '↑' : '↓'} {Math.abs(trend)}% vs last period
        </div>
      )}
    </div>
  );
}
