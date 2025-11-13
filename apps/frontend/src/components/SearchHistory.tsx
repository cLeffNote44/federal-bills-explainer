'use client';

import { useEffect, useState } from 'react';

interface SearchHistoryItem {
  query: string;
  timestamp: string;
  results_count?: number;
  filters?: Record<string, any>;
}

interface SearchHistoryProps {
  onSelectQuery: (query: string) => void;
}

export default function SearchHistory({ onSelectQuery }: SearchHistoryProps) {
  const [history, setHistory] = useState<SearchHistoryItem[]>([]);
  const [popularSearches, setPopularSearches] = useState<Array<{ query: string; count: number }>>([]);
  const [loading, setLoading] = useState(true);

  const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    fetchHistory();
    fetchPopularSearches();
  }, []);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_URL}/search/history/my`);
      const data = await response.json();
      setHistory(data.history || []);
    } catch (error) {
      console.error('Error fetching search history:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPopularSearches = async () => {
    try {
      const response = await fetch(`${API_URL}/search/history/popular?limit=10`);
      const data = await response.json();
      setPopularSearches(data.popular_searches || []);
    } catch (error) {
      console.error('Error fetching popular searches:', error);
    }
  };

  const clearHistory = async () => {
    try {
      await fetch(`${API_URL}/search/history/my`, { method: 'DELETE' });
      setHistory([]);
    } catch (error) {
      console.error('Error clearing history:', error);
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      const now = new Date();
      const diffMs = now.getTime() - date.getTime();
      const diffMins = Math.floor(diffMs / 60000);
      const diffHours = Math.floor(diffMs / 3600000);
      const diffDays = Math.floor(diffMs / 86400000);

      if (diffMins < 1) return 'Just now';
      if (diffMins < 60) return `${diffMins}m ago`;
      if (diffHours < 24) return `${diffHours}h ago`;
      if (diffDays < 7) return `${diffDays}d ago`;
      return date.toLocaleDateString();
    } catch {
      return timestamp;
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded w-1/4"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-10 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-6">Search History</h2>

      {/* Recent Searches */}
      {history.length > 0 ? (
        <div className="mb-8">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-gray-700">Recent Searches</h3>
            <button
              onClick={clearHistory}
              className="text-sm text-fed-blue hover:text-blue-700"
            >
              Clear All
            </button>
          </div>
          <div className="space-y-2">
            {history.map((item, index) => (
              <div
                key={index}
                onClick={() => onSelectQuery(item.query)}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-fed-blue cursor-pointer transition-colors group"
              >
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <svg className="h-4 w-4 text-gray-400 group-hover:text-fed-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-sm font-medium text-gray-900 group-hover:text-fed-blue">
                      {item.query}
                    </span>
                  </div>
                  {item.results_count !== undefined && (
                    <span className="text-xs text-gray-500 ml-6">
                      {item.results_count} results
                    </span>
                  )}
                </div>
                <span className="text-xs text-gray-500">
                  {formatTimestamp(item.timestamp)}
                </span>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8 mb-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <p className="mt-2 text-sm text-gray-600">No search history yet</p>
        </div>
      )}

      {/* Popular Searches */}
      {popularSearches.length > 0 && (
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-3">Popular Searches</h3>
          <div className="space-y-2">
            {popularSearches.map((item, index) => (
              <div
                key={index}
                onClick={() => onSelectQuery(item.query)}
                className="flex items-center justify-between p-3 rounded-lg border border-gray-200 hover:border-fed-blue cursor-pointer transition-colors group"
              >
                <div className="flex items-center gap-2">
                  <svg className="h-4 w-4 text-gray-400 group-hover:text-fed-blue" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                  </svg>
                  <span className="text-sm font-medium text-gray-900 group-hover:text-fed-blue">
                    {item.query}
                  </span>
                </div>
                <span className="text-xs text-gray-500">{item.count} searches</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
