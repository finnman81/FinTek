import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { ClerkProvider } from '@clerk/nextjs';
import './globals.css';

const inter = Inter({ subsets: ['latin'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'Anchorpoint | Fin-Tek Ozone',
  description: 'Anchorpoint – Fin-Tek Ozone industrial knowledge assistant',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const publishableKey = process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY;
  const body = (
    <>
      <nav className="border-b border-anchor-navy/10 bg-anchor-navy px-5 py-3 flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <span className="text-white font-bold tracking-widest uppercase text-sm">
            Anchorpoint
          </span>
          <span className="text-anchor-cyan/70 text-xs tracking-wide">
            Systems
          </span>
        </div>
        <div className="flex gap-5 text-sm font-medium">
          <a href="/" className="text-anchor-cyan hover:text-white transition-colors">
            Chat
          </a>
          <a href="/upload" className="text-gray-400 hover:text-white transition-colors">
            Upload
          </a>
          <a href="/admin" className="text-gray-400 hover:text-white transition-colors">
            Admin
          </a>
        </div>
      </nav>
      {children}
    </>
  );
  return (
    <html lang="en" className={inter.variable}>
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
