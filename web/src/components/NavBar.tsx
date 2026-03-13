'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';
import { useTenant } from '@/lib/tenant-context';

const NAV_ITEMS = [
  { href: '/', label: 'Chat' },
  { href: '/upload', label: 'Upload' },
  { href: '/admin', label: 'Admin' },
];

export default function NavBar() {
  const pathname = usePathname();
  const { tenantId, setTenantId } = useTenant();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-white/10 bg-anchor-navy">
      <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3 sm:px-6">
        {/* Brand */}
        <Link href="/" className="flex items-baseline gap-1.5 select-none">
          <span className="text-white font-bold tracking-wide text-base">
            Munitor
          </span>
          <span className="text-anchor-cyan font-semibold text-sm tracking-wide">
            AI
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden sm:flex items-center gap-1">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {label}
              </Link>
            );
          })}

          {/* Tenant settings button */}
          <div className="relative ml-3">
            <button
              type="button"
              onClick={() => setSettingsOpen(!settingsOpen)}
              className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-colors ${
                tenantId
                  ? 'text-anchor-green hover:bg-white/5'
                  : 'text-amber-400 hover:bg-white/5'
              }`}
              title={tenantId ? `Tenant: ${tenantId.slice(0, 8)}…` : 'Set tenant ID'}
            >
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.343 3.94c.09-.542.56-.94 1.11-.94h1.093c.55 0 1.02.398 1.11.94l.149.894c.07.424.384.764.78.93s.844.083 1.168-.166l.717-.537a1.125 1.125 0 0 1 1.6.18l.774.774a1.125 1.125 0 0 1 .18 1.6l-.537.717c-.249.324-.282.782-.166 1.168.116.396.456.71.88.78l.894.149c.542.09.94.56.94 1.11v1.093c0 .55-.398 1.02-.94 1.11l-.894.149c-.424.07-.764.384-.93.78s-.083.844.166 1.168l.537.717a1.125 1.125 0 0 1-.18 1.6l-.774.774a1.125 1.125 0 0 1-1.6.18l-.717-.537c-.324-.249-.782-.282-1.168-.166-.396.116-.71.456-.78.88l-.149.894c-.09.542-.56.94-1.11.94h-1.093c-.55 0-1.02-.398-1.11-.94l-.149-.894c-.07-.424-.384-.764-.78-.93s-.844-.083-1.168.166l-.717.537a1.125 1.125 0 0 1-1.6-.18l-.774-.774a1.125 1.125 0 0 1-.18-1.6l.537-.717c.249-.324.282-.782.166-1.168a1.125 1.125 0 0 0-.78-.88l-.894-.149c-.542-.09-.94-.56-.94-1.11v-1.093c0-.55.398-1.02.94-1.11l.894-.149c.424-.07.764-.384.93-.78s.083-.844-.166-1.168l-.537-.717a1.125 1.125 0 0 1 .18-1.6l.774-.774a1.125 1.125 0 0 1 1.6.18l.717.537c.324.249.782.282 1.168.166.396-.116.71-.456.78-.88l.149-.894Z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z" />
              </svg>
              {tenantId ? (
                <span className="hidden lg:inline text-xs text-gray-400 font-mono">
                  {tenantId.slice(0, 8)}…
                </span>
              ) : (
                <span className="text-xs">Set tenant</span>
              )}
            </button>

            {settingsOpen && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setSettingsOpen(false)} />
                <div className="absolute right-0 z-50 mt-2 w-80 rounded-lg border border-white/10 bg-anchor-navy shadow-xl p-4">
                  <label className="block text-xs font-medium text-gray-400 mb-1.5">
                    Tenant ID
                  </label>
                  <input
                    type="text"
                    value={tenantId}
                    onChange={(e) => setTenantId(e.target.value)}
                    placeholder="e.g. 00000000-0000-0000-0000-000000000001"
                    className="w-full rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50"
                  />
                  <p className="mt-2 text-xs text-gray-500">
                    Required for API calls. Set via environment variable or enter manually.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="sm:hidden rounded-md p-2 text-gray-400 hover:text-white hover:bg-white/5"
          aria-label="Toggle menu"
        >
          {mobileOpen ? (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M6 18 18 6M6 6l12 12" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu panel */}
      {mobileOpen && (
        <div className="sm:hidden border-t border-white/10 px-4 pb-3 pt-2 space-y-1">
          {NAV_ITEMS.map(({ href, label }) => {
            const active = pathname === href;
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setMobileOpen(false)}
                className={`block rounded-md px-3 py-2 text-sm font-medium transition-colors ${
                  active
                    ? 'bg-white/10 text-white'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'
                }`}
              >
                {label}
              </Link>
            );
          })}
          <div className="border-t border-white/10 pt-3 mt-2">
            <label className="block text-xs font-medium text-gray-400 mb-1.5 px-3">
              Tenant ID
            </label>
            <input
              type="text"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              placeholder="Enter tenant UUID"
              className="mx-3 w-[calc(100%-1.5rem)] rounded-md border border-white/10 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50"
            />
          </div>
        </div>
      )}
    </nav>
  );
}
