'use client';

import { useState, useEffect } from 'react';
import { usageStats, listDocuments } from '@/lib/api';
import { useTenant } from '@/lib/tenant-context';
import Link from 'next/link';

type UsageData = {
  total_queries: number;
  total_tokens: number;
  avg_confidence: number;
  low_confidence_queries: number;
};

const STAT_CARDS: { key: keyof UsageData; label: string; icon: string }[] = [
  { key: 'total_queries', label: 'Total Queries', icon: '💬' },
  { key: 'total_tokens', label: 'Total Tokens', icon: '🔤' },
  { key: 'avg_confidence', label: 'Avg Confidence', icon: '🎯' },
  { key: 'low_confidence_queries', label: 'Low Confidence', icon: '⚠️' },
];

export default function AdminPage() {
  const { tenantId } = useTenant();
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [docs, setDocs] = useState<Array<{ id: string; filename: string; status: string; chunk_count: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    Promise.all([usageStats(tenantId), listDocuments(tenantId)])
      .then(([u, d]) => { setUsage(u); setDocs(d); })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [tenantId]);

  const needsTenant = !tenantId;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6">
      <h1 className="text-xl font-bold text-anchor-navy mb-6">Admin</h1>

      {needsTenant && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Set a Tenant ID in the nav settings to view admin data.
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {/* Usage stats */}
      <section className="mb-6 rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-5 py-3">
          <h2 className="font-semibold text-anchor-navy text-sm">Usage</h2>
        </div>
        {loading && !usage ? (
          <div className="px-5 py-8 text-center">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-anchor-cyan" />
          </div>
        ) : usage ? (
          <div className="grid grid-cols-2 gap-3 p-4">
            {STAT_CARDS.map(({ key, label, icon }) => (
              <div key={key} className="rounded-lg border border-gray-100 bg-anchor-light/50 p-3">
                <div className="flex items-center gap-1.5 mb-1">
                  <span className="text-base">{icon}</span>
                  <span className="text-xs font-medium uppercase tracking-wide text-anchor-dark/40">
                    {label}
                  </span>
                </div>
                <p className="text-xl font-semibold text-anchor-navy tabular-nums">
                  {typeof usage[key] === 'number' && key === 'avg_confidence'
                    ? usage[key].toFixed(2)
                    : usage[key]}
                </p>
              </div>
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center py-10 text-center">
            <svg className="mb-3 h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <p className="text-sm font-medium text-anchor-dark/60">No usage data</p>
            <p className="mt-1 text-xs text-anchor-dark/40">
              {needsTenant
                ? 'Configure a tenant ID to see usage statistics.'
                : 'Start asking questions in Chat to generate usage data.'}
            </p>
          </div>
        )}
      </section>

      {/* Document overview */}
      <section className="rounded-xl border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-100 px-5 py-3 flex items-center justify-between">
          <h2 className="font-semibold text-anchor-navy text-sm">
            Documents {docs.length > 0 && <span className="text-anchor-dark/40 font-normal">({docs.length})</span>}
          </h2>
          {docs.length > 0 && (
            <Link href="/upload" className="text-xs text-anchor-cyan hover:text-anchor-blue transition-colors">
              Manage →
            </Link>
          )}
        </div>
        <div className="divide-y divide-gray-50">
          {docs.map((d) => (
            <div key={d.id} className="flex items-center justify-between px-5 py-3">
              <span className="text-sm font-medium text-anchor-dark truncate">{d.filename}</span>
              <span className="text-xs text-anchor-dark/40 flex-shrink-0 ml-3">
                {d.status}{d.chunk_count > 0 ? ` · ${d.chunk_count} chunks` : ''}
              </span>
            </div>
          ))}
          {docs.length === 0 && (
            <div className="flex flex-col items-center py-10 text-center">
              <svg className="mb-3 h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <p className="text-sm font-medium text-anchor-dark/60">No documents</p>
              <p className="mt-1 text-xs text-anchor-dark/40">
                {needsTenant
                  ? 'Configure a tenant ID to manage documents.'
                  : 'Upload documents to build your knowledge base.'}
              </p>
              {!needsTenant && (
                <Link
                  href="/upload"
                  className="mt-3 inline-flex items-center rounded-lg bg-anchor-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-anchor-navy"
                >
                  Go to Upload
                </Link>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
