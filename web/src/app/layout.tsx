import type { Metadata, Viewport } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import MobileNav from '@/components/MobileNav';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',
  themeColor: '#102A43',
};

export const metadata: Metadata = {
  title: 'Anchorpoint | Fin-Tek Ozone',
  description: 'Anchorpoint – Fin-Tek Ozone industrial knowledge assistant',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'black-translucent',
    title: 'Anchorpoint',
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const body = (
    <>
      <MobileNav />
      {children}
    </>
  );
  return (
    <html lang="en" className={inter.variable}>
      <head>
        <link rel="apple-touch-icon" href="/icons/apple-touch-icon.png" />
      </head>
      <body className={`min-h-screen bg-anchor-light antialiased text-anchor-dark ${inter.className}`}>
        {publishableKey ? (
          <ClerkProvider publishableKey={publishableKey}>
            {body}
          </ClerkProvider>
        ) : (
          body
        )}
      </body>
    </html>
  );
}
