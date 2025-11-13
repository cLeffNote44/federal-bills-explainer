/**
 * Touch gesture utilities and hooks for mobile interactions
 */

import { useEffect, useRef, RefObject } from 'react';

interface SwipeConfig {
  onSwipeLeft?: () => void;
  onSwipeRight?: () => void;
  onSwipeUp?: () => void;
  onSwipeDown?: () => void;
  threshold?: number;
}

/**
 * Hook for detecting swipe gestures
 */
export function useSwipe(config: SwipeConfig) {
  const {
    onSwipeLeft,
    onSwipeRight,
    onSwipeUp,
    onSwipeDown,
    threshold = 50,
  } = config;

  const touchStart = useRef({ x: 0, y: 0 });
  const touchEnd = useRef({ x: 0, y: 0 });

  const handleTouchStart = (e: TouchEvent) => {
    touchStart.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    };
  };

  const handleTouchMove = (e: TouchEvent) => {
    touchEnd.current = {
      x: e.touches[0].clientX,
      y: e.touches[0].clientY,
    };
  };

  const handleTouchEnd = () => {
    const deltaX = touchEnd.current.x - touchStart.current.x;
    const deltaY = touchEnd.current.y - touchStart.current.y;

    const absDeltaX = Math.abs(deltaX);
    const absDeltaY = Math.abs(deltaY);

    // Horizontal swipe
    if (absDeltaX > absDeltaY && absDeltaX > threshold) {
      if (deltaX > 0 && onSwipeRight) {
        onSwipeRight();
      } else if (deltaX < 0 && onSwipeLeft) {
        onSwipeLeft();
      }
    }

    // Vertical swipe
    if (absDeltaY > absDeltaX && absDeltaY > threshold) {
      if (deltaY > 0 && onSwipeDown) {
        onSwipeDown();
      } else if (deltaY < 0 && onSwipeUp) {
        onSwipeUp();
      }
    }
  };

  useEffect(() => {
    document.addEventListener('touchstart', handleTouchStart);
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [onSwipeLeft, onSwipeRight, onSwipeUp, onSwipeDown]);
}

/**
 * Hook for detecting long press
 */
export function useLongPress(
  callback: () => void,
  options: {
    threshold?: number;
    onStart?: () => void;
    onFinish?: () => void;
    onCancel?: () => void;
  } = {}
) {
  const { threshold = 500, onStart, onFinish, onCancel } = options;
  const isLongPress = useRef(false);
  const timerRef = useRef<NodeJS.Timeout>();
  const target = useRef<EventTarget>();

  const start = (event: React.TouchEvent | React.MouseEvent) => {
    target.current = event.target;
    isLongPress.current = false;

    if (onStart) {
      onStart();
    }

    timerRef.current = setTimeout(() => {
      isLongPress.current = true;
      callback();
      if (onFinish) {
        onFinish();
      }
    }, threshold);
  };

  const stop = () => {
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    if (!isLongPress.current && onCancel) {
      onCancel();
    }
  };

  return {
    onMouseDown: start,
    onMouseUp: stop,
    onMouseLeave: stop,
    onTouchStart: start,
    onTouchEnd: stop,
  };
}

/**
 * Hook for detecting pull-to-refresh gesture
 */
export function usePullToRefresh(
  onRefresh: () => Promise<void>,
  options: {
    threshold?: number;
    enabled?: boolean;
  } = {}
) {
  const { threshold = 80, enabled = true } = options;
  const startY = useRef(0);
  const currentY = useRef(0);
  const isRefreshing = useRef(false);
  const pullDistance = useRef(0);

  useEffect(() => {
    if (!enabled) return;

    const handleTouchStart = (e: TouchEvent) => {
      // Only trigger if scrolled to top
      if (window.scrollY === 0) {
        startY.current = e.touches[0].clientY;
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (isRefreshing.current || window.scrollY > 0) return;

      currentY.current = e.touches[0].clientY;
      pullDistance.current = currentY.current - startY.current;

      // Prevent default scroll if pulling down
      if (pullDistance.current > 0) {
        e.preventDefault();
        // Could add visual feedback here
      }
    };

    const handleTouchEnd = async () => {
      if (pullDistance.current > threshold && !isRefreshing.current) {
        isRefreshing.current = true;

        try {
          await onRefresh();
        } finally {
          isRefreshing.current = false;
          pullDistance.current = 0;
        }
      } else {
        pullDistance.current = 0;
      }
    };

    document.addEventListener('touchstart', handleTouchStart, { passive: true });
    document.addEventListener('touchmove', handleTouchMove, { passive: false });
    document.addEventListener('touchend', handleTouchEnd);

    return () => {
      document.removeEventListener('touchstart', handleTouchStart);
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [enabled, onRefresh, threshold]);
}

/**
 * Hook for detecting tap/double tap
 */
export function useTap(
  onSingleTap?: () => void,
  onDoubleTap?: () => void,
  delay: number = 300
) {
  const tapCount = useRef(0);
  const timerRef = useRef<NodeJS.Timeout>();

  const handleTap = () => {
    tapCount.current += 1;

    if (tapCount.current === 1) {
      timerRef.current = setTimeout(() => {
        if (tapCount.current === 1 && onSingleTap) {
          onSingleTap();
        }
        tapCount.current = 0;
      }, delay);
    } else if (tapCount.current === 2) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }

      if (onDoubleTap) {
        onDoubleTap();
      }

      tapCount.current = 0;
    }
  };

  return {
    onClick: handleTap,
    onTouchEnd: handleTap,
  };
}

/**
 * Hook for detecting pinch zoom gesture
 */
export function usePinchZoom(
  onPinch: (scale: number) => void,
  elementRef: RefObject<HTMLElement>
) {
  const initialDistance = useRef(0);
  const currentScale = useRef(1);

  useEffect(() => {
    const element = elementRef.current;
    if (!element) return;

    const handleTouchStart = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        initialDistance.current = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );
      }
    };

    const handleTouchMove = (e: TouchEvent) => {
      if (e.touches.length === 2) {
        e.preventDefault();
        const touch1 = e.touches[0];
        const touch2 = e.touches[1];
        const currentDistance = Math.hypot(
          touch2.clientX - touch1.clientX,
          touch2.clientY - touch1.clientY
        );

        const scale = currentDistance / initialDistance.current;
        currentScale.current = scale;
        onPinch(scale);
      }
    };

    element.addEventListener('touchstart', handleTouchStart, { passive: false });
    element.addEventListener('touchmove', handleTouchMove, { passive: false });

    return () => {
      element.removeEventListener('touchstart', handleTouchStart);
      element.removeEventListener('touchmove', handleTouchMove);
    };
  }, [elementRef, onPinch]);
}

/**
 * Detect if device supports touch
 */
export function isTouchDevice(): boolean {
  if (typeof window === 'undefined') return false;

  return (
    'ontouchstart' in window ||
    navigator.maxTouchPoints > 0 ||
    (navigator as any).msMaxTouchPoints > 0
  );
}

/**
 * Get optimal touch target size (44x44 minimum for accessibility)
 */
export function getTouchTargetSize(size: number = 44): { width: number; height: number } {
  const minSize = 44; // iOS Human Interface Guidelines
  return {
    width: Math.max(size, minSize),
    height: Math.max(size, minSize),
  };
}

/**
 * Prevent default touch behavior (like zoom on double tap)
 */
export function preventDefaultTouch(element: HTMLElement) {
  element.addEventListener('touchstart', (e) => {
    if (e.touches.length > 1) {
      e.preventDefault();
    }
  }, { passive: false });
}
