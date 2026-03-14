'use client';

import { useState, useEffect } from 'react';
import { usageStats, listDocuments, knowledgeGaps } from '@/lib/api';
import { useTenant } from '@/lib/tenant-context';
import Link from 'next/link';

type UsageData = {
  total_queries: number;
  total_tokens: number;
  avg_confidence: number;
  low_confidence_queries: number;
};

type DocItem = { id: string; filename: string; status: string; chunk_count: number };

const STAT_CARDS: { key: keyof UsageData; label: string; format?: 'decimal' }[] = [
  { key: 'total_queries', label: 'Total Queries' },
  { key: 'total_tokens', label: 'Total Tokens' },
  { key: 'avg_confidence', label: 'Avg Confidence', format: 'decimal' },
  { key: 'low_confidence_queries', label: 'Low Confidence' },
];

const STATUS_BAR_COLORS: Record<string, string> = {
  completed: 'bg-emerald-500',
  processing: 'bg-amber-500',
  pending: 'bg-slate-400',
  failed: 'bg-red-500',
};

const STATUS_LABEL_COLORS: Record<string, string> = {
  completed: 'text-emerald-700',
  processing: 'text-amber-700',
  pending: 'text-slate-600',
  failed: 'text-red-700',
};

function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.min(Math.max(value * 100, 0), 100);
  const color = pct >= 70 ? 'text-emerald-500' : pct >= 40 ? 'text-amber-500' : 'text-red-500';
  const trackColor = pct >= 70 ? 'stroke-emerald-100' : pct >= 40 ? 'stroke-amber-100' : 'stroke-red-100';
  const strokeColor = pct >= 70 ? 'stroke-emerald-500' : pct >= 40 ? 'stroke-amber-500' : 'stroke-red-500';
  const circumference = 2 * Math.PI * 36;
  const offset = circumference - (pct / 100) * circumference;

  return (
    <div className="flex flex-col items-center" role="meter" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Confidence score">
      <svg className="h-24 w-24 -rotate-90" viewBox="0 0 80 80" aria-hidden="true">
        <circle cx="40" cy="40" r="36" fill="none" strokeWidth="6" className={trackColor} />
        <circle
          cx="40" cy="40" r="36" fill="none" strokeWidth="6"
          className={strokeColor}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: 'stroke-dashoffset 0.6s ease' }}
        />
      </svg>
      <span className={`-mt-[3.6rem] text-lg font-bold tabular-nums ${color}`}>
        {pct.toFixed(0)}%
      </span>
      <span className="mt-6 text-xs text-anchor-dark/50 font-medium">Confidence</span>
    </div>
  );
}

function StatusDistribution({ docs }: { docs: DocItem[] }) {
  if (docs.length === 0) return null;
  const counts: Record<string, number> = {};
  docs.forEach((d) => { counts[d.status] = (counts[d.status] || 0) + 1; });
  const statuses = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  const total = docs.length;

  return (
    <div role="img" aria-label={`Document status: ${statuses.map(([s, c]) => `${c} ${s}`).join(', ')}`}>
      <div className="flex h-3 w-full overflow-hidden rounded-full bg-gray-100">
        {statuses.map(([status, count]) => (
          <div
            key={status}
            className={`${STATUS_BAR_COLORS[status] || 'bg-gray-400'} transition-all duration-500`}
            style={{ width: `${(count / total) * 100}%` }}
          />
        ))}
      </div>
      <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1">
        {statuses.map(([status, count]) => (
          <div key={status} className="flex items-center gap-1.5 text-xs">
            <span className={`h-2 w-2 rounded-full ${STATUS_BAR_COLORS[status] || 'bg-gray-400'}`} aria-hidden="true" />
            <span className={`font-medium ${STATUS_LABEL_COLORS[status] || 'text-gray-600'}`}>
              {status.charAt(0).toUpperCase() + status.slice(1)}
            </span>
            <span className="text-anchor-dark/40">{count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AdminPage() {
  const { tenantId } = useTenant();
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [docs, setDocs] = useState<DocItem[]>([]);
  const [gaps, setGaps] = useState<Array<{ question: string; confidence: number }>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenantId) return;
    setLoading(true);
    setError(null);
    Promise.all([usageStats(tenantId), listDocuments(tenantId), knowledgeGaps(tenantId)])
      .then(([u, d, g]) => { setUsage(u); setDocs(d); setGaps(g); })
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load'))
      .finally(() => setLoading(false));
  }, [tenantId]);

  const needsTenant = !tenantId;
  const totalChunks = docs.reduce((sum, d) => sum + (d.chunk_count || 0), 0);

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6" role="region" aria-label="Admin dashboard">
      <h1 className="text-xl font-bold text-anchor-navy mb-6">Admin</h1>

      {needsTenant && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800" role="alert">
          Set a Tenant ID in the nav settings to view admin data.
        </div>
      )}

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {/* Usage stats + confidence gauge */}
      <section className="mb-6 rounded-xl border border-gray-200 bg-white shadow-sm" aria-label="Usage statistics">
        <div className="border-b border-gray-100 px-5 py-3">
          <h2 className="font-semibold text-anchor-navy text-sm">Usage Overview</h2>
        </div>
        {loading && !usage ? (
          <div className="px-5 py-8 text-center" aria-label="Loading">
            <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-anchor-cyan" />
          </div>
        ) : usage ? (
          <div className="p-4">
            <div className="flex flex-col sm:flex-row gap-4">
              {/* Stat cards */}
              <div className="grid grid-cols-2 gap-3 flex-1">
                {STAT_CARDS.map(({ key, label, format }) => (
                  <div key={key} className="rounded-lg border border-gray-100 bg-anchor-light/50 p-3">
                    <span className="text-xs font-medium uppercase tracking-wide text-anchor-dark/50">
                      {label}
                    </span>
                    <p className="mt-1 text-xl font-semibold text-anchor-navy tabular-nums">
                      {format === 'decimal' ? usage[key].toFixed(2) : usage[key].toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
              {/* Confidence gauge */}
              <div className="flex items-center justify-center sm:w-36">
                <ConfidenceGauge value={usage.avg_confidence} />
              </div>
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center py-10 text-center">
            <svg className="mb-3 h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 0 1 3 19.875v-6.75ZM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V8.625ZM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 0 1-1.125-1.125V4.125Z" />
            </svg>
            <p className="text-sm font-medium text-anchor-dark/60">No usage data</p>
            <p className="mt-1 text-xs text-anchor-dark/50">
              {needsTenant ? 'Configure a tenant ID to see usage statistics.' : 'Start asking questions in Chat to generate usage data.'}
            </p>
          </div>
        )}
      </section>

      {/* Document overview + status distribution chart */}
      <section className="mb-6 rounded-xl border border-gray-200 bg-white shadow-sm" aria-label="Document overview">
        <div className="border-b border-gray-100 px-5 py-3 flex items-center justify-between">
          <h2 className="font-semibold text-anchor-navy text-sm">
            Documents {docs.length > 0 && <span className="text-anchor-dark/40 font-normal">({docs.length})</span>}
          </h2>
          {docs.length > 0 && (
            <Link href="/upload" className="text-xs text-anchor-cyan hover:text-anchor-blue transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan rounded">
              Manage →
            </Link>
          )}
        </div>
        <div className="p-4">
          {docs.length > 0 ? (
            <div className="space-y-4">
              {/* Summary row */}
              <div className="flex gap-6 text-sm">
                <div>
                  <span className="text-anchor-dark/50 text-xs">Documents</span>
                  <p className="font-semibold text-anchor-navy tabular-nums">{docs.length}</p>
                </div>
                <div>
                  <span className="text-anchor-dark/50 text-xs">Total Chunks</span>
                  <p className="font-semibold text-anchor-navy tabular-nums">{totalChunks.toLocaleString()}</p>
                </div>
              </div>
              {/* Status bar chart */}
              <StatusDistribution docs={docs} />
            </div>
          ) : (
            <div className="flex flex-col items-center py-8 text-center">
              <svg className="mb-3 h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
              </svg>
              <p className="text-sm font-medium text-anchor-dark/60">No documents</p>
              <p className="mt-1 text-xs text-anchor-dark/50">
                {needsTenant ? 'Configure a tenant ID to manage documents.' : 'Upload documents to build your knowledge base.'}
              </p>
              {!needsTenant && (
                <Link href="/upload" className="mt-3 inline-flex items-center rounded-lg bg-anchor-blue px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-anchor-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan focus-visible:ring-offset-2">
                  Go to Upload
                </Link>
              )}
            </div>
          )}
        </div>
      </section>

      {/* Knowledge gaps */}
      <section className="rounded-xl border border-gray-200 bg-white shadow-sm" aria-label="Knowledge gaps">
        <div className="border-b border-gray-100 px-5 py-3">
          <h2 className="font-semibold text-anchor-navy text-sm">Knowledge Gaps</h2>
        </div>
        <div className="p-4">
          {gaps.length > 0 ? (
            <ul className="space-y-2" role="list">
              {gaps.map((g, i) => (
                <li key={i} className="flex items-center justify-between rounded-lg border border-gray-100 bg-anchor-light/50 px-3 py-2 text-sm">
                  <span className="text-anchor-dark truncate mr-3">{g.question}</span>
                  <span className="text-xs text-anchor-dark/40 tabular-nums flex-shrink-0">{(g.confidence * 100).toFixed(0)}%</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="flex flex-col items-center py-8 text-center">
              <svg className="mb-3 h-9 w-9 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9 5.25h.008v.008H12v-.008Z" />
              </svg>
              <p className="text-sm font-medium text-anchor-dark/60">No knowledge gaps detected</p>
              <p className="mt-1 text-xs text-anchor-dark/50">
                Low-confidence queries will appear here as users ask questions.
              </p>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
