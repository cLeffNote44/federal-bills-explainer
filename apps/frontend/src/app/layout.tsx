import type { Metadata, Viewport } from 'next';
import { ThemeProvider, AuthProvider } from '@/contexts';
import { MobileNav } from '@/components';
import './globals.css';

export const metadata: Metadata = {
  title: 'Federal Bills Explainer',
  description: 'Understand US federal legislation with plain-language explanations',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'Federal Bills',
  },
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://federalbills.app',
    siteName: 'Federal Bills Explainer',
    title: 'Federal Bills Explainer',
    description: 'Understand US federal legislation with plain-language explanations',
    images: [
      {
        url: '/og-image.png',
        width: 1200,
        height: 630,
        alt: 'Federal Bills Explainer',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Federal Bills Explainer',
    description: 'Understand US federal legislation with plain-language explanations',
    images: ['/og-image.png'],
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#003f88' },
    { media: '(prefers-color-scheme: dark)', color: '#1a1a2e' },
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/favicon.ico" sizes="any" />
        <link rel="icon" href="/icon.svg" type="image/svg+xml" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
      </head>
      <body className="antialiased pb-16 sm:pb-0">
        <ThemeProvider>
          <AuthProvider>
            {children}
            <MobileNav />
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
