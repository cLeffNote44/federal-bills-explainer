/**
 * Frontend Analytics Tracking
 *
 * Provides client-side event tracking for user interactions.
 * Events are sent to the analytics backend for aggregation.
 */

interface EventData {
  event_name: string;
  event_category?: string;
  event_label?: string;
  event_value?: number;
  user_agent?: string;
  page_url?: string;
  referrer?: string;
  timestamp?: string;
  [key: string]: any;
}

interface AnalyticsConfig {
  apiUrl: string;
  enabled: boolean;
  debug: boolean;
}

class Analytics {
  private config: AnalyticsConfig;
  private queue: EventData[] = [];
  private flushInterval: NodeJS.Timeout | null = null;

  constructor(config?: Partial<AnalyticsConfig>) {
    this.config = {
      apiUrl: config?.apiUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
      enabled: config?.enabled ?? true,
      debug: config?.debug ?? false,
    };

    // Start flush interval (every 10 seconds)
    if (typeof window !== 'undefined' && this.config.enabled) {
      this.flushInterval = setInterval(() => this.flush(), 10000);
    }
  }

  /**
   * Track a custom event
   */
  track(eventName: string, data?: Partial<EventData>) {
    if (!this.config.enabled) return;

    const event: EventData = {
      event_name: eventName,
      event_category: data?.event_category,
      event_label: data?.event_label,
      event_value: data?.event_value,
      user_agent: typeof navigator !== 'undefined' ? navigator.userAgent : undefined,
      page_url: typeof window !== 'undefined' ? window.location.href : undefined,
      referrer: typeof document !== 'undefined' ? document.referrer : undefined,
      timestamp: new Date().toISOString(),
      ...data,
    };

    this.queue.push(event);

    if (this.config.debug) {
      console.log('[Analytics] Event tracked:', event);
    }

    // Flush immediately if queue is large
    if (this.queue.length >= 10) {
      this.flush();
    }
  }

  /**
   * Track a page view
   */
  pageView(pageName?: string) {
    this.track('page_view', {
      event_category: 'navigation',
      event_label: pageName || (typeof window !== 'undefined' ? window.location.pathname : undefined),
    });
  }

  /**
   * Track a search query
   */
  search(query: string, resultsCount?: number) {
    this.track('search', {
      event_category: 'search',
      event_label: query,
      event_value: resultsCount,
      search_query: query,
      results_count: resultsCount,
    });
  }

  /**
   * Track a bill view
   */
  billView(billId: string, billTitle?: string) {
    this.track('bill_view', {
      event_category: 'content',
      event_label: billId,
      bill_id: billId,
      bill_title: billTitle,
    });
  }

  /**
   * Track an export action
   */
  export(format: 'csv' | 'json', itemCount?: number) {
    this.track('export', {
      event_category: 'export',
      event_label: format,
      event_value: itemCount,
      export_format: format,
      item_count: itemCount,
    });
  }

  /**
   * Track filter usage
   */
  filter(filterType: string, filterValue: string) {
    this.track('filter', {
      event_category: 'interaction',
      event_label: `${filterType}:${filterValue}`,
      filter_type: filterType,
      filter_value: filterValue,
    });
  }

  /**
   * Track errors
   */
  error(errorMessage: string, errorStack?: string, context?: any) {
    this.track('error', {
      event_category: 'error',
      event_label: errorMessage,
      error_message: errorMessage,
      error_stack: errorStack,
      context: context,
    });
  }

  /**
   * Track performance metrics
   */
  performance(metricName: string, value: number, unit: string = 'ms') {
    this.track('performance', {
      event_category: 'performance',
      event_label: metricName,
      event_value: value,
      metric_name: metricName,
      metric_value: value,
      metric_unit: unit,
    });
  }

  /**
   * Track user engagement
   */
  engagement(action: string, target?: string, value?: number) {
    this.track('engagement', {
      event_category: 'engagement',
      event_label: action,
      event_value: value,
      action: action,
      target: target,
    });
  }

  /**
   * Flush queued events to the backend
   */
  private async flush() {
    if (this.queue.length === 0) return;

    const events = [...this.queue];
    this.queue = [];

    if (this.config.debug) {
      console.log('[Analytics] Flushing events:', events.length);
    }

    try {
      // Note: This endpoint would need to be implemented on the backend
      // For now, we'll just log in debug mode
      if (this.config.debug) {
        console.log('[Analytics] Events to send:', events);
      }

      // Uncomment when backend endpoint is ready
      // await fetch(`${this.config.apiUrl}/analytics/events`, {
      //   method: 'POST',
      //   headers: { 'Content-Type': 'application/json' },
      //   body: JSON.stringify({ events }),
      // });
    } catch (error) {
      console.error('[Analytics] Failed to send events:', error);
      // Re-queue events on failure
      this.queue.unshift(...events);
    }
  }

  /**
   * Cleanup - call on unmount
   */
  destroy() {
    if (this.flushInterval) {
      clearInterval(this.flushInterval);
      this.flushInterval = null;
    }
    this.flush();
  }
}

// Create singleton instance
let analyticsInstance: Analytics | null = null;

export function getAnalytics(): Analytics {
  if (!analyticsInstance) {
    analyticsInstance = new Analytics();
  }
  return analyticsInstance;
}

// Convenience functions
export const trackEvent = (eventName: string, data?: Partial<EventData>) =>
  getAnalytics().track(eventName, data);

export const trackPageView = (pageName?: string) =>
  getAnalytics().pageView(pageName);

export const trackSearch = (query: string, resultsCount?: number) =>
  getAnalytics().search(query, resultsCount);

export const trackBillView = (billId: string, billTitle?: string) =>
  getAnalytics().billView(billId, billTitle);

export const trackExport = (format: 'csv' | 'json', itemCount?: number) =>
  getAnalytics().export(format, itemCount);

export const trackFilter = (filterType: string, filterValue: string) =>
  getAnalytics().filter(filterType, filterValue);

export const trackError = (errorMessage: string, errorStack?: string, context?: any) =>
  getAnalytics().error(errorMessage, errorStack, context);

export const trackPerformance = (metricName: string, value: number, unit?: string) =>
  getAnalytics().performance(metricName, value, unit);

export const trackEngagement = (action: string, target?: string, value?: number) =>
  getAnalytics().engagement(action, target, value);

// React hook for analytics
import { useEffect } from 'react';

export function useAnalytics() {
  const analytics = getAnalytics();

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      analytics.destroy();
    };
  }, []);

  return analytics;
}

// Track page views automatically
export function usePageTracking() {
  useEffect(() => {
    trackPageView();
  }, []);
}
