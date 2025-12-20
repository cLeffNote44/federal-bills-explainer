'use client';

import { useState, useEffect } from 'react';
import { api } from '@/lib/api';
import { TimelineSkeleton } from './Skeleton';

interface TimelineEvent {
  id: string;
  date: string;
  title: string;
  description?: string;
  type: 'introduced' | 'committee' | 'vote' | 'passed' | 'signed' | 'vetoed' | 'other';
}

interface BillTimelineProps {
  billId: string;
  congress: number;
  billType: string;
  number: number;
  introducedDate?: string;
  latestActionDate?: string;
  status?: string;
  publicLawNumber?: string;
  className?: string;
}

const eventTypeConfig: Record<
  TimelineEvent['type'],
  { color: string; bgColor: string; icon: React.ReactNode }
> = {
  introduced: {
    color: 'text-blue-600 dark:text-blue-400',
    bgColor: 'bg-blue-100 dark:bg-blue-900',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    ),
  },
  committee: {
    color: 'text-purple-600 dark:text-purple-400',
    bgColor: 'bg-purple-100 dark:bg-purple-900',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
  },
  vote: {
    color: 'text-orange-600 dark:text-orange-400',
    bgColor: 'bg-orange-100 dark:bg-orange-900',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
      </svg>
    ),
  },
  passed: {
    color: 'text-green-600 dark:text-green-400',
    bgColor: 'bg-green-100 dark:bg-green-900',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
      </svg>
    ),
  },
  signed: {
    color: 'text-green-700 dark:text-green-300',
    bgColor: 'bg-green-200 dark:bg-green-800',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
      </svg>
    ),
  },
  vetoed: {
    color: 'text-red-600 dark:text-red-400',
    bgColor: 'bg-red-100 dark:bg-red-900',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
      </svg>
    ),
  },
  other: {
    color: 'text-gray-600 dark:text-gray-400',
    bgColor: 'bg-gray-100 dark:bg-gray-800',
    icon: (
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
};

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function generateTimelineFromProps(props: BillTimelineProps): TimelineEvent[] {
  const events: TimelineEvent[] = [];

  if (props.introducedDate) {
    events.push({
      id: 'introduced',
      date: props.introducedDate,
      title: 'Bill Introduced',
      description: `${props.billType.toUpperCase()}-${props.number} was introduced in Congress ${props.congress}`,
      type: 'introduced',
    });
  }

  // Add committee referral (simulated - in real app would come from API)
  if (props.status?.toLowerCase().includes('committee')) {
    events.push({
      id: 'committee',
      date: props.introducedDate || new Date().toISOString(),
      title: 'Referred to Committee',
      description: 'Bill was referred to relevant committee(s) for review',
      type: 'committee',
    });
  }

  // If passed (has public law number)
  if (props.publicLawNumber) {
    events.push({
      id: 'passed-house',
      date: props.latestActionDate || new Date().toISOString(),
      title: 'Passed Both Chambers',
      description: 'Bill passed both the House and Senate',
      type: 'passed',
    });
    events.push({
      id: 'signed',
      date: props.latestActionDate || new Date().toISOString(),
      title: 'Signed into Law',
      description: `Became Public Law ${props.publicLawNumber}`,
      type: 'signed',
    });
  }

  // Latest action
  if (props.latestActionDate && !props.publicLawNumber) {
    events.push({
      id: 'latest',
      date: props.latestActionDate,
      title: 'Latest Action',
      description: props.status || 'Action taken on bill',
      type: 'other',
    });
  }

  // Sort by date
  return events.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
}

export default function BillTimeline(props: BillTimelineProps) {
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    // Try to fetch detailed timeline from API
    const fetchTimeline = async () => {
      try {
        const data = await api
          .get(`bills/${props.congress}/${props.billType}/${props.number}/timeline`)
          .json<TimelineEvent[]>();
        setEvents(data);
      } catch {
        // Fall back to generated timeline from props
        setEvents(generateTimelineFromProps(props));
      } finally {
        setLoading(false);
      }
    };

    fetchTimeline();
  }, [props.congress, props.billType, props.number]);

  if (loading) {
    return (
      <div className={props.className}>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          Bill Timeline
        </h3>
        <TimelineSkeleton count={3} />
      </div>
    );
  }

  if (events.length === 0) {
    return (
      <div className={`${props.className} text-center py-8`}>
        <p className="text-gray-500 dark:text-gray-400">
          No timeline information available
        </p>
      </div>
    );
  }

  const displayEvents = expanded ? events : events.slice(0, 4);

  return (
    <div className={props.className}>
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        Bill Timeline
      </h3>

      <div className="relative">
        {displayEvents.map((event, index) => {
          const config = eventTypeConfig[event.type];
          const isLast = index === displayEvents.length - 1;

          return (
            <div key={event.id} className="flex gap-4 pb-6">
              {/* Timeline connector */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center ${config.bgColor} ${config.color}`}
                >
                  {config.icon}
                </div>
                {!isLast && (
                  <div className="w-0.5 flex-1 bg-gray-200 dark:bg-gray-700 mt-2" />
                )}
              </div>

              {/* Event content */}
              <div className="flex-1 pb-2">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                    {event.title}
                  </span>
                  <span className="text-xs text-gray-500 dark:text-gray-400">
                    {formatDate(event.date)}
                  </span>
                </div>
                {event.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {event.description}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {events.length > 4 && (
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-sm font-medium text-fed-blue dark:text-blue-400 hover:underline"
        >
          {expanded ? 'Show less' : `Show ${events.length - 4} more events`}
        </button>
      )}
    </div>
  );
}
