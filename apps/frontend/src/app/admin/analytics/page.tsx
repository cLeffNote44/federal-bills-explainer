'use client';

import { Container, AnalyticsTrendsChart, ErrorAnalytics, UserAgentAnalytics } from '@/components';

export default function AnalyticsPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Container>
        <div className="py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Advanced Analytics</h1>
            <p className="text-gray-600">Detailed insights into API usage, errors, and user behavior</p>
          </div>

          {/* Analytics Sections */}
          <div className="space-y-8">
            {/* Request Trends */}
            <AnalyticsTrendsChart hours={24} />

            {/* User Agent Analytics */}
            <UserAgentAnalytics />

            {/* Error Analytics */}
            <ErrorAnalytics limit={20} />
          </div>
        </div>
      </Container>
    </div>
  );
}
