import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { Providers } from "@/components/providers";
import { AuthModal } from "@/components/shared/auth-modal";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "Federal Bills Explainer",
    template: "%s | Federal Bills Explainer",
  },
  description:
    "AI-powered platform that makes federal legislation accessible through plain-language explanations and semantic search.",
  keywords: ["federal bills", "legislation", "congress", "AI", "civic tech"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-background text-foreground">
        <Providers>
          {children}
          <AuthModal />
        </Providers>
      </body>
    </html>
  );
}
