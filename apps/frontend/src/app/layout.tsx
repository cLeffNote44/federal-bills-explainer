import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Federal Bills Explainer',
  description: 'Understand US federal legislation',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
