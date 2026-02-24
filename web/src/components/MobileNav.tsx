'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

const NAV_LINKS = [
  { href: '/', label: 'Chat' },
  { href: '/upload', label: 'Upload' },
  { href: '/admin', label: 'Admin' },
];

export default function MobileNav() {
  const [open, setOpen] = useState(false);
  const pathname = usePathname();

  return (
    <nav className="border-b border-anchor-navy/10 bg-anchor-navy px-5 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-baseline gap-2.5">
          <span className="text-white font-bold tracking-widest uppercase text-sm">
            Anchorpoint
          </span>
          <span className="text-anchor-cyan/70 text-xs tracking-wide">
            Systems
          </span>
        </div>

        {/* Desktop links */}
        <div className="hidden sm:flex gap-5 text-sm font-medium">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className={`transition-colors ${
                pathname === link.href
                  ? 'text-anchor-cyan'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setOpen(!open)}
          className="sm:hidden flex flex-col justify-center items-center w-10 h-10 rounded-lg hover:bg-white/10 transition-colors"
          aria-label={open ? 'Close menu' : 'Open menu'}
          aria-expanded={open}
        >
          <span
            className={`block w-5 h-0.5 bg-white transition-transform duration-200 ${
              open ? 'rotate-45 translate-y-[3px]' : ''
            }`}
          />
          <span
            className={`block w-5 h-0.5 bg-white mt-1 transition-opacity duration-200 ${
              open ? 'opacity-0' : ''
            }`}
          />
          <span
            className={`block w-5 h-0.5 bg-white mt-1 transition-transform duration-200 ${
              open ? '-rotate-45 -translate-y-[7px]' : ''
            }`}
          />
        </button>
      </div>

      {/* Mobile dropdown */}
      {open && (
        <div className="sm:hidden mt-3 pb-1 flex flex-col gap-1">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              onClick={() => setOpen(false)}
              className={`block px-3 py-3 rounded-lg text-sm font-medium transition-colors ${
                pathname === link.href
                  ? 'text-anchor-cyan bg-white/5'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              {link.label}
            </Link>
          ))}
        </div>
      )}
    </nav>
  );
}
