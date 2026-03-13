import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import NavBar from '@/components/NavBar';
import { TenantProvider } from '@/lib/tenant-context';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Munitor AI',
  description: 'Munitor AI – industrial knowledge assistant for equipment service companies',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;

  const inner = (
    <TenantProvider>
      <NavBar />
      <main className="flex-1">{children}</main>
    </TenantProvider>
  );

  return (
    <html lang="en" className={inter.variable}>
      <body
        className={`flex min-h-screen flex-col bg-anchor-light antialiased text-anchor-dark ${inter.className}`}
      >
        {publishableKey ? (
          <ClerkProvider publishableKey={publishableKey}>{inner}</ClerkProvider>
        ) : (
          inner
        )}
      </body>
    </html>
  );
}
