import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import NavBar from '@/components/NavBar';
import { TenantProvider } from '@/lib/tenant-context';
import { Toaster } from 'sonner';
import AuthProvider from '@/components/AuthProvider';
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
  return (
    <html lang="en" className={inter.variable}>
      <body
        className={`flex min-h-screen flex-col bg-anchor-light antialiased text-anchor-dark ${inter.className}`}
      >
        <AuthProvider>
          <TenantProvider>
            <a
              href="#main-content"
              className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:rounded-lg focus:bg-anchor-navy focus:px-4 focus:py-2 focus:text-sm focus:font-medium focus:text-white focus:shadow-lg"
            >
              Skip to main content
            </a>
            <NavBar />
            <main id="main-content" className="flex-1" role="main">
              {children}
            </main>
            <Toaster position="bottom-right" richColors closeButton />
          </TenantProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
