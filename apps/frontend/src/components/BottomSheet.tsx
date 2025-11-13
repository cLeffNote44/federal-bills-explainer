'use client';

import { useEffect, useRef, ReactNode } from 'react';
import { useSwipeable } from 'react-swipeable';

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  snapPoints?: number[];
  className?: string;
}

export default function BottomSheet({
  isOpen,
  onClose,
  children,
  title,
  snapPoints = [0.9],
  className = '',
}: BottomSheetProps) {
  const sheetRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);
  const dragStartY = useRef(0);
  const currentTranslate = useRef(0);

  // Prevent body scroll when sheet is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      // Set initial position
      if (sheetRef.current) {
        const windowHeight = window.innerHeight;
        const snapHeight = windowHeight * (1 - snapPoints[0]);
        sheetRef.current.style.transform = `translateY(${snapHeight}px)`;
      }
    } else {
      document.body.style.overflow = '';
    }

    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen, snapPoints]);

  const handlers = useSwipeable({
    onSwipedDown: (eventData) => {
      // Close if swiped down far enough
      if (eventData.deltaY > 100) {
        onClose();
      }
    },
    trackMouse: true,
  });

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black bg-opacity-50 z-40 transition-opacity duration-300"
        onClick={onClose}
        style={{ touchAction: 'none' }}
      />

      {/* Bottom Sheet */}
      <div
        ref={sheetRef}
        className={`
          fixed bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-2xl z-50
          transform transition-transform duration-300 ease-out
          max-h-[90vh] flex flex-col
          ${className}
        `}
        style={{ touchAction: 'pan-y' }}
      >
        {/* Handle */}
        <div
          {...handlers}
          className="flex justify-center py-3 cursor-grab active:cursor-grabbing"
        >
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
        </div>

        {/* Header */}
        {title && (
          <div className="flex items-center justify-between px-6 pb-4 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
            <button
              onClick={onClose}
              className="p-2 rounded-full text-gray-500 hover:bg-gray-100 transition-colors"
              aria-label="Close"
            >
              <svg
                className="h-6 w-6"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
          </div>
        )}

        {/* Content */}
        <div
          ref={contentRef}
          className="flex-1 overflow-y-auto overscroll-contain px-6 py-4"
          style={{ WebkitOverflowScrolling: 'touch' }}
        >
          {children}
        </div>
      </div>
    </>
  );
}
