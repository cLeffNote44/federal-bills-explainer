'use client';

import { useEffect, ReactNode } from 'react';
import { registerServiceWorker } from '@/lib/pwa';
import { InstallPrompt } from '@/components';

export default function PWAProvider({ children }: { children: ReactNode }) {
  useEffect(() => {
    // Register service worker
    if ('serviceWorker' in navigator) {
      registerServiceWorker();
    }

    // Handle online/offline status
    const handleOnline = () => {
      console.log('App is online');
      // Could show a notification or update UI
    };

    const handleOffline = () => {
      console.log('App is offline');
      // Could show offline indicator
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <>
      {children}
      <InstallPrompt />
    </>
  );
}
