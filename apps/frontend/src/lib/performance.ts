/**
 * Performance monitoring utilities for tracking Core Web Vitals and custom metrics.
 */

// Core Web Vitals types
interface WebVital {
  name: string;
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
  delta: number;
  id: string;
}

/**
 * Report Web Vitals to analytics service.
 * Can be integrated with Google Analytics, DataDog, etc.
 */
export function reportWebVitals(metric: WebVital) {
  // Log in development
  if (process.env.NODE_ENV === 'development') {
    console.log(`[Web Vital] ${metric.name}:`, {
      value: metric.value,
      rating: metric.rating,
      delta: metric.delta,
    });
  }

  // Send to analytics in production
  if (process.env.NODE_ENV === 'production') {
    // Example: Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', metric.name, {
        value: Math.round(metric.value),
        event_category: 'Web Vitals',
        event_label: metric.id,
        non_interaction: true,
      });
    }

    // Example: Custom analytics endpoint
    if (typeof window !== 'undefined' && navigator.sendBeacon) {
      const body = JSON.stringify({
        metric: metric.name,
        value: metric.value,
        rating: metric.rating,
        page: window.location.pathname,
        timestamp: Date.now(),
      });

      navigator.sendBeacon('/api/analytics/vitals', body);
    }
  }
}

/**
 * Measure custom performance metrics.
 */
export class PerformanceMonitor {
  private marks: Map<string, number> = new Map();

  /**
   * Start timing a custom metric.
   */
  start(name: string): void {
    this.marks.set(name, performance.now());
  }

  /**
   * End timing and log the duration.
   */
  end(name: string): number | null {
    const startTime = this.marks.get(name);
    if (!startTime) {
      console.warn(`No start mark found for "${name}"`);
      return null;
    }

    const duration = performance.now() - startTime;
    this.marks.delete(name);

    if (process.env.NODE_ENV === 'development') {
      console.log(`[Performance] ${name}: ${duration.toFixed(2)}ms`);
    }

    return duration;
  }

  /**
   * Measure async operation.
   */
  async measure<T>(name: string, fn: () => Promise<T>): Promise<T> {
    this.start(name);
    try {
      const result = await fn();
      this.end(name);
      return result;
    } catch (error) {
      this.end(name);
      throw error;
    }
  }
}

/**
 * Global performance monitor instance.
 */
export const perfMonitor = new PerformanceMonitor();

/**
 * Check if Performance API is available.
 */
export function isPerformanceSupported(): boolean {
  return typeof window !== 'undefined' && 'performance' in window;
}

/**
 * Get navigation timing metrics.
 */
export function getNavigationTiming() {
  if (!isPerformanceSupported()) return null;

  const perfData = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
  if (!perfData) return null;

  return {
    // DNS lookup time
    dns: perfData.domainLookupEnd - perfData.domainLookupStart,
    // TCP connection time
    tcp: perfData.connectEnd - perfData.connectStart,
    // Request time
    request: perfData.responseStart - perfData.requestStart,
    // Response time
    response: perfData.responseEnd - perfData.responseStart,
    // DOM processing time
    domProcessing: perfData.domComplete - perfData.domInteractive,
    // Total load time
    loadComplete: perfData.loadEventEnd - perfData.fetchStart,
  };
}

/**
 * Prefetch a URL for faster navigation.
 */
export function prefetchUrl(url: string): void {
  if (typeof document === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = url;
  document.head.appendChild(link);
}

/**
 * Preconnect to a domain for faster requests.
 */
export function preconnect(url: string): void {
  if (typeof document === 'undefined') return;

  const link = document.createElement('link');
  link.rel = 'preconnect';
  link.href = url;
  document.head.appendChild(link);
}

/**
 * Check if user prefers reduced motion.
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/**
 * Check if connection is slow (2G, slow-2g).
 */
export function isSlowConnection(): boolean {
  if (typeof navigator === 'undefined' || !('connection' in navigator)) {
    return false;
  }

  const connection = (navigator as any).connection;
  return connection && (connection.effectiveType === 'slow-2g' || connection.effectiveType === '2g');
}

/**
 * Check if user is on a metered connection (Save-Data header).
 */
export function isSaveDataEnabled(): boolean {
  if (typeof navigator === 'undefined' || !('connection' in navigator)) {
    return false;
  }

  const connection = (navigator as any).connection;
  return connection && connection.saveData === true;
}

/**
 * Get recommended quality level based on connection.
 */
export function getRecommendedQuality(): 'low' | 'medium' | 'high' {
  if (isSaveDataEnabled() || isSlowConnection()) {
    return 'low';
  }

  if (typeof navigator !== 'undefined' && 'connection' in navigator) {
    const connection = (navigator as any).connection;
    if (connection && connection.effectiveType === '4g') {
      return 'high';
    }
  }

  return 'medium';
}
