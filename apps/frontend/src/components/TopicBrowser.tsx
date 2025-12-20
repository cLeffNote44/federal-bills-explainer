'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';
import { Skeleton } from './Skeleton';

interface Topic {
  name: string;
  count: number;
  icon?: string;
}

interface TopicBrowserProps {
  selectedTopic?: string;
  onSelectTopic?: (topic: string | null) => void;
  variant?: 'sidebar' | 'grid' | 'chips';
  className?: string;
}

// Predefined topic icons and colors
const topicConfig: Record<string, { icon: string; color: string }> = {
  healthcare: { icon: '🏥', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' },
  defense: { icon: '🛡️', color: 'bg-slate-100 dark:bg-slate-900/30 text-slate-700 dark:text-slate-300' },
  education: { icon: '📚', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300' },
  economy: { icon: '💰', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' },
  environment: { icon: '🌿', color: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300' },
  infrastructure: { icon: '🏗️', color: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300' },
  immigration: { icon: '🌐', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300' },
  technology: { icon: '💻', color: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300' },
  agriculture: { icon: '🌾', color: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300' },
  veterans: { icon: '🎖️', color: 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' },
  judiciary: { icon: '⚖️', color: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' },
  energy: { icon: '⚡', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' },
  default: { icon: '📋', color: 'bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-300' },
};

function getTopicConfig(topicName: string) {
  const key = topicName.toLowerCase().replace(/\s+/g, '');
  return topicConfig[key] || topicConfig.default;
}

export default function TopicBrowser({
  selectedTopic,
  onSelectTopic,
  variant = 'chips',
  className = '',
}: TopicBrowserProps) {
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchTopics = async () => {
      try {
        const data = await api.get('topics').json<Topic[]>();
        setTopics(data);
      } catch {
        // Fall back to sample topics
        setTopics([
          { name: 'Healthcare', count: 156 },
          { name: 'Defense', count: 89 },
          { name: 'Education', count: 134 },
          { name: 'Economy', count: 201 },
          { name: 'Environment', count: 98 },
          { name: 'Infrastructure', count: 67 },
          { name: 'Immigration', count: 45 },
          { name: 'Technology', count: 78 },
        ]);
      } finally {
        setLoading(false);
      }
    };

    fetchTopics();
  }, []);

  if (loading) {
    if (variant === 'chips') {
      return (
        <div className={`flex flex-wrap gap-2 ${className}`}>
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className="w-24 h-8 rounded-full" />
          ))}
        </div>
      );
    }
    return (
      <div className={className}>
        {Array.from({ length: 8 }).map((_, i) => (
          <Skeleton key={i} className="w-full h-10 mb-2" />
        ))}
      </div>
    );
  }

  if (variant === 'chips') {
    return (
      <div className={`flex flex-wrap gap-2 ${className}`}>
        {/* All topics chip */}
        <button
          onClick={() => onSelectTopic?.(null)}
          className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
            !selectedTopic
              ? 'bg-fed-blue text-white'
              : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
          }`}
        >
          All Topics
        </button>

        {topics.map((topic) => {
          const config = getTopicConfig(topic.name);
          const isSelected = selectedTopic === topic.name;

          return (
            <button
              key={topic.name}
              onClick={() => onSelectTopic?.(isSelected ? null : topic.name)}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors flex items-center gap-2 ${
                isSelected
                  ? 'bg-fed-blue text-white'
                  : `${config.color} hover:opacity-80`
              }`}
            >
              <span>{config.icon}</span>
              <span>{topic.name}</span>
              <span
                className={`text-xs ${
                  isSelected ? 'text-blue-200' : 'opacity-60'
                }`}
              >
                {topic.count}
              </span>
            </button>
          );
        })}
      </div>
    );
  }

  if (variant === 'sidebar') {
    return (
      <div className={`space-y-1 ${className}`}>
        <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-3">
          Browse by Topic
        </h3>

        <button
          onClick={() => onSelectTopic?.(null)}
          className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
            !selectedTopic
              ? 'bg-fed-blue text-white'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
          }`}
        >
          All Bills
        </button>

        {topics.map((topic) => {
          const config = getTopicConfig(topic.name);
          const isSelected = selectedTopic === topic.name;

          return (
            <button
              key={topic.name}
              onClick={() => onSelectTopic?.(isSelected ? null : topic.name)}
              className={`w-full text-left px-3 py-2 rounded-lg transition-colors flex items-center justify-between ${
                isSelected
                  ? 'bg-fed-blue text-white'
                  : 'hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300'
              }`}
            >
              <span className="flex items-center gap-2">
                <span>{config.icon}</span>
                <span>{topic.name}</span>
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full ${
                  isSelected
                    ? 'bg-white/20 text-white'
                    : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                }`}
              >
                {topic.count}
              </span>
            </button>
          );
        })}
      </div>
    );
  }

  // Grid variant
  return (
    <div className={`grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4 ${className}`}>
      {topics.map((topic) => {
        const config = getTopicConfig(topic.name);

        return (
          <button
            key={topic.name}
            onClick={() => onSelectTopic?.(topic.name)}
            className={`p-4 rounded-xl transition-all hover:shadow-md ${config.color} ${
              selectedTopic === topic.name ? 'ring-2 ring-fed-blue' : ''
            }`}
          >
            <div className="text-3xl mb-2">{config.icon}</div>
            <div className="font-semibold">{topic.name}</div>
            <div className="text-sm opacity-60">{topic.count} bills</div>
          </button>
        );
      })}
    </div>
  );
}
