'use client';

import { useState, useEffect } from 'react';
import { listDocuments, uploadDocument, documentStatus } from '@/lib/api';
import Link from 'next/link';

const DEFAULT_TENANT = process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID || '';

export default function UploadPage() {
  const [tenantId, setTenantId] = useState(DEFAULT_TENANT);
  const [docs, setDocs] = useState<Array<{ id: string; filename: string; status: string; chunk_count: number }>>([]);
  const [uploading, setUploading] = useState(false);
  const [polling, setPolling] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(false);

  function refreshDocs() {
    if (!tenantId) return;
    setLoadingDocs(true);
    setError(null);
    listDocuments(tenantId)
      .then(setDocs)
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Failed to load documents');
      })
      .finally(() => setLoadingDocs(false));
  }

  useEffect(() => {
    refreshDocs();
  }, [tenantId]);

  useEffect(() => {
    if (polling.size === 0) return;
    const t = setInterval(() => {
      polling.forEach((docId) => {
        documentStatus(tenantId, docId).then((s) => {
          if (s.status === 'completed' || s.status === 'failed') {
            setPolling((prev) => {
              const next = new Set(prev);
              next.delete(docId);
              return next;
            });
            refreshDocs();
          }
        });
      });
    }, 2000);
    return () => clearInterval(t);
  }, [polling, tenantId]);

  async function onFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !tenantId) return;
    setUploading(true);
    setError(null);
    try {
      const { document_id } = await uploadDocument(tenantId, file);
      setPolling((prev) => new Set(prev).add(document_id));
      refreshDocs();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setUploading(false);
      e.target.value = '';
    }
  }

  return (
    <div className="min-h-screen bg-anchor-light">
      <div className="max-w-2xl mx-auto px-4 py-6">
        <div className="flex items-center gap-4 mb-6">
          <Link href="/" className="text-anchor-cyan hover:text-anchor-blue transition-colors text-sm">
            &larr; Chat
          </Link>
          <h1 className="text-xl font-bold text-anchor-navy">Upload documents</h1>
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

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5 mb-6">
          <label className="block text-sm font-medium text-anchor-navy mb-2">Choose file</label>
          <input
            type="file"
            accept=".pdf,.docx,.txt,.csv,.md"
            onChange={onFileSelect}
            disabled={uploading || !tenantId}
            className="block w-full text-sm text-anchor-dark file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-anchor-blue file:text-white hover:file:bg-anchor-navy file:transition-colors file:cursor-pointer"
          />
          {uploading && <p className="mt-2 text-anchor-cyan text-sm animate-pulse">Uploading and queuing...</p>}
          {error && <p className="mt-2 text-red-600 text-sm" role="alert">{error}</p>}
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-5">
          <h2 className="font-semibold text-anchor-navy mb-3">Documents</h2>
          {loadingDocs && docs.length === 0 && <p className="text-anchor-dark/50 text-sm">Loading...</p>}
          <ul className="space-y-2">
            {docs.map((d) => (
              <li key={d.id} className="flex justify-between items-center p-3 bg-anchor-light rounded-lg text-sm">
                <span className="text-anchor-dark font-medium">{d.filename}</span>
                <span className="text-anchor-dark/60">
                  {polling.has(d.id) ? 'Processing...' : `${d.status}${d.chunk_count ? `, ${d.chunk_count} chunks` : ''}`}
                </span>
              </li>
            ))}
            {docs.length === 0 && <li className="text-anchor-dark/50 text-sm">No documents yet.</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
