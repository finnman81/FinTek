'use client';

import { useState, useEffect } from 'react';
import { usageStats, listDocuments } from '@/lib/api';
import Link from 'next/link';

const DEFAULT_TENANT = process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID || '';

export default function AdminPage() {
  const [tenantId, setTenantId] = useState(DEFAULT_TENANT);
  const [usage, setUsage] = useState<{ total_queries: number; total_tokens: number; avg_confidence: number; low_confidence_queries: number } | null>(null);
  const [docs, setDocs] = useState<Array<{ id: string; filename: string; status: string; chunk_count: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    Promise.all([usageStats(tenantId), listDocuments(tenantId)])
      .then(([u, d]) => {
        setUsage(u);
        setDocs(d);
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [tenantId]);

  return (
    <div className="min-h-[calc(100dvh-56px)] bg-anchor-light">
      <div className="max-w-2xl mx-auto px-4 py-4 sm:py-6">
        <div className="flex items-center gap-4 mb-4 sm:mb-6">
          <Link href="/" className="text-anchor-cyan hover:text-anchor-blue transition-colors text-sm py-2">
            &larr; Chat
          </Link>
          <h1 className="text-lg sm:text-xl font-bold text-anchor-navy">Admin</h1>
        </div>

        {!tenantId && (
          <div className="mb-4 p-3 bg-anchor-cyan/10 border border-anchor-cyan/30 rounded-lg">
            <label className="block text-sm font-medium text-anchor-navy">Tenant ID</label>
            <input
              type="text"
              value={tenantId}
              onChange={(e) => setTenantId(e.target.value)}
              className="mt-1 block w-full rounded-lg border border-anchor-cyan/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50"
            />
          </div>
        )}

        {error && <p className="mb-4 text-red-600 text-sm" role="alert">{error}</p>}

        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5 mb-4 sm:mb-6">
          <h2 className="font-semibold text-anchor-navy mb-3">Usage</h2>
          {loading && !usage ? (
            <p className="text-anchor-dark/50 text-sm animate-pulse">Loading...</p>
          ) : usage ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
              <div className="p-3 bg-anchor-light rounded-lg border border-gray-100">
                <p className="text-anchor-dark/50 text-xs uppercase tracking-wide mb-1">Total queries</p>
                <p className="text-anchor-navy font-semibold text-lg">{usage.total_queries}</p>
              </div>
              <div className="p-3 bg-anchor-light rounded-lg border border-gray-100">
                <p className="text-anchor-dark/50 text-xs uppercase tracking-wide mb-1">Total tokens</p>
                <p className="text-anchor-navy font-semibold text-lg">{usage.total_tokens}</p>
              </div>
              <div className="p-3 bg-anchor-light rounded-lg border border-gray-100">
                <p className="text-anchor-dark/50 text-xs uppercase tracking-wide mb-1">Avg confidence</p>
                <p className="text-anchor-navy font-semibold text-lg">{usage.avg_confidence}</p>
              </div>
              <div className="p-3 bg-anchor-light rounded-lg border border-gray-100">
                <p className="text-anchor-dark/50 text-xs uppercase tracking-wide mb-1">Low-confidence</p>
                <p className="text-anchor-navy font-semibold text-lg">{usage.low_confidence_queries}</p>
              </div>
            </div>
          ) : (
            <p className="text-anchor-dark/50 text-sm">Enter a tenant ID to load usage.</p>
          )}
        </section>

        <section className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 sm:p-5">
          <h2 className="font-semibold text-anchor-navy mb-3">Documents</h2>
          <ul className="space-y-2">
            {docs.map((d) => (
              <li key={d.id} className="flex flex-col sm:flex-row sm:justify-between gap-1 sm:gap-2 p-3 bg-anchor-light rounded-lg text-sm">
                <span className="text-anchor-dark font-medium truncate">{d.filename}</span>
                <span className="text-anchor-dark/60 text-xs sm:text-sm shrink-0">{d.status}, {d.chunk_count} chunks</span>
              </li>
            ))}
            {docs.length === 0 && <li className="text-anchor-dark/50 text-sm">No documents.</li>}
          </ul>
        </section>
      </div>
    </div>
  );
}
