'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Unhandled error:', error);
  }, [error]);

  return (
    <div className="flex flex-1 flex-col items-center justify-center px-4 py-16 text-center" role="alert">
      <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-red-50">
        <svg className="h-7 w-7 text-red-500" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z" />
        </svg>
      </div>
      <h2 className="text-lg font-semibold text-anchor-navy">Something went wrong</h2>
      <p className="mt-1 max-w-sm text-sm text-anchor-dark/60">
        An unexpected error occurred. Please try again or contact support if the problem persists.
      </p>
      {error.digest && (
        <p className="mt-2 font-mono text-xs text-anchor-dark/30">Error ID: {error.digest}</p>
      )}
      <button
        type="button"
        onClick={reset}
        className="mt-5 rounded-lg bg-anchor-blue px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-anchor-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan focus-visible:ring-offset-2"
      >
        Try again
      </button>
    </div>
  );
}
