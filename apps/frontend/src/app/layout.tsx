import type { Metadata, Viewport } from 'next';
import './globals.css';
import PWAProvider from './pwa-provider';

export const metadata: Metadata = {
  title: {
    default: 'Federal Bills Explainer',
    template: '%s | Federal Bills Explainer',
  },
  description: 'AI-powered platform for understanding US federal legislation. Search, filter, and explore bills with plain-English explanations.',
  keywords: ['federal bills', 'legislation', 'congress', 'government', 'AI', 'politics'],
  authors: [{ name: 'Federal Bills Explainer' }],
  creator: 'Federal Bills Explainer',
  publisher: 'Federal Bills Explainer',
  applicationName: 'Federal Bills Explainer',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Bills Explainer',
  },
  formatDetection: {
    telephone: false,
  },
  icons: {
    icon: [
      { url: '/icons/icon-192x192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icons/icon-512x512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: [
      { url: '/icons/icon-152x152.png', sizes: '152x152', type: 'image/png' },
    ],
  },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  themeColor: '#1e40af',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#1e40af" />
        <link rel="apple-touch-icon" href="/icons/icon-192x192.png" />
      </head>
      <body>
        <PWAProvider>{children}</PWAProvider>
      </body>
    </html>
  );
}
