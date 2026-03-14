'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { listDocuments, uploadDocument, documentStatus, deleteDocument } from '@/lib/api';
import { useTenant } from '@/lib/tenant-context';

const STATUS_COLORS: Record<string, string> = {
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  processing: 'bg-amber-50 text-amber-700 border-amber-200',
  pending: 'bg-slate-50 text-slate-600 border-slate-200',
  failed: 'bg-red-50 text-red-700 border-red-200',
};

const STATUS_DOT: Record<string, string> = {
  completed: 'bg-emerald-500',
  processing: 'bg-amber-500 animate-pulse',
  pending: 'bg-slate-400',
  failed: 'bg-red-500',
};

const FILE_ICONS: Record<string, string> = {
  '.pdf': '📄', '.docx': '📝', '.txt': '📃', '.csv': '📊', '.md': '📋',
};

export default function UploadPage() {
  const { tenantId } = useTenant();
  const [docs, setDocs] = useState<Array<{ id: string; filename: string; status: string; chunk_count: number }>>([]);
  const [uploading, setUploading] = useState(false);
  const [polling, setPolling] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string | null>(null);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refreshDocs = useCallback(() => {
    if (!tenantId) return;
    setLoadingDocs(true);
    setError(null);
    listDocuments(tenantId)
      .then(setDocs)
      .catch((err) => setError(err instanceof Error ? err.message : 'Failed to load documents'))
      .finally(() => setLoadingDocs(false));
  }, [tenantId]);

  useEffect(() => { refreshDocs(); }, [refreshDocs]);

  useEffect(() => {
    if (polling.size === 0) return;
    const t = setInterval(() => {
      polling.forEach((docId) => {
        documentStatus(tenantId, docId).then((s) => {
          if (s.status === 'completed' || s.status === 'failed') {
            setPolling((prev) => { const next = new Set(prev); next.delete(docId); return next; });
            refreshDocs();
          }
        });
      });
    }, 2000);
    return () => clearInterval(t);
  }, [polling, tenantId, refreshDocs]);

  async function handleFile(file: File) {
    if (!tenantId) return;
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
    }
  }

  async function handleDelete(docId: string) {
    if (!tenantId) return;
    setDeleting(docId);
    setError(null);
    try {
      await deleteDocument(tenantId, docId);
      setDocs((prev) => prev.filter((d) => d.id !== docId));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Delete failed');
    } finally {
      setDeleting(null);
      setConfirmDelete(null);
    }
  }

  function onFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
    e.target.value = '';
  }

  function onDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  }

  function getExt(filename: string) {
    const dot = filename.lastIndexOf('.');
    return dot >= 0 ? filename.slice(dot).toLowerCase() : '';
  }

  const needsTenant = !tenantId;

  return (
    <div className="mx-auto w-full max-w-3xl px-4 py-6 sm:px-6" role="region" aria-label="Document upload">
      <h1 className="text-xl font-bold text-anchor-navy mb-6">Upload Documents</h1>

      {needsTenant && (
        <div className="mb-6 rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800" role="alert">
          Set a Tenant ID in the nav settings to upload documents.
        </div>
      )}

      {/* Drag-and-drop zone */}
      <div
        role="button"
        tabIndex={needsTenant || uploading ? -1 : 0}
        aria-label="Upload area — drag and drop a file or click to browse"
        aria-disabled={needsTenant || uploading}
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        onClick={() => !needsTenant && !uploading && fileRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); !needsTenant && !uploading && fileRef.current?.click(); } }}
        className={`relative mb-6 flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan ${
          needsTenant
            ? 'border-gray-200 bg-gray-50 cursor-not-allowed opacity-60'
            : dragOver
              ? 'border-anchor-cyan bg-anchor-cyan/5'
              : 'border-gray-300 bg-white hover:border-anchor-cyan/50 hover:bg-anchor-cyan/5'
        }`}
      >
        <input
          ref={fileRef}
          type="file"
          accept=".pdf,.docx,.txt,.csv,.md"
          onChange={onFileSelect}
          disabled={uploading || needsTenant}
          className="hidden"
          aria-hidden="true"
          tabIndex={-1}
        />
        {uploading ? (
          <>
            <svg className="mb-3 h-8 w-8 animate-spin text-anchor-cyan" fill="none" viewBox="0 0 24 24" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <p className="text-sm font-medium text-anchor-navy">Uploading…</p>
          </>
        ) : (
          <>
            <svg className="mb-3 h-8 w-8 text-gray-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 16.5V9.75m0 0 3 3m-3-3-3 3M6.75 19.5a4.5 4.5 0 0 1-1.41-8.775 5.25 5.25 0 0 1 10.233-2.33 3 3 0 0 1 3.758 3.848A3.752 3.752 0 0 1 18 19.5H6.75Z" />
            </svg>
            <p className="text-sm font-medium text-anchor-navy">
              {dragOver ? 'Drop file here' : 'Drag & drop a file, or click to browse'}
            </p>
            <p className="mt-1 text-xs text-anchor-dark/50">PDF, DOCX, TXT, CSV, or Markdown</p>
          </>
        )}
      </div>

      {error && (
        <div className="mb-6 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
          {error}
        </div>
      )}

      {/* Document list */}
      <div className="rounded-xl border border-gray-200 bg-white shadow-sm" role="region" aria-label="Document list">
        <div className="border-b border-gray-100 px-5 py-3">
          <h2 className="font-semibold text-anchor-navy text-sm">
            Documents {docs.length > 0 && <span className="text-anchor-dark/40 font-normal">({docs.length})</span>}
          </h2>
        </div>
        <ul className="divide-y divide-gray-50" role="list">
          {loadingDocs && docs.length === 0 && (
            <li className="px-5 py-8 text-center" aria-label="Loading documents">
              <div className="mx-auto h-6 w-6 animate-spin rounded-full border-2 border-gray-200 border-t-anchor-cyan" />
            </li>
          )}
          {docs.map((d) => {
            const st = polling.has(d.id) ? 'processing' : d.status;
            return (
              <li key={d.id} className="group flex items-center justify-between px-5 py-3 hover:bg-gray-50/50 transition-colors">
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className="text-lg flex-shrink-0" aria-hidden="true">{FILE_ICONS[getExt(d.filename)] || '📄'}</span>
                  <span className="text-sm font-medium text-anchor-dark truncate">{d.filename}</span>
                </div>
                <div className="flex items-center gap-2 flex-shrink-0 ml-3">
                  {d.chunk_count > 0 && (
                    <span className="hidden sm:inline text-xs text-anchor-dark/40">{d.chunk_count} chunks</span>
                  )}
                  <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium ${STATUS_COLORS[st] || STATUS_COLORS.pending}`}>
                    <span className={`h-1.5 w-1.5 rounded-full ${STATUS_DOT[st] || STATUS_DOT.pending}`} aria-hidden="true" />
                    {st === 'processing' ? 'Processing…' : st.charAt(0).toUpperCase() + st.slice(1)}
                  </span>

                  {/* Delete button */}
                  {confirmDelete === d.id ? (
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        onClick={() => handleDelete(d.id)}
                        disabled={deleting === d.id}
                        aria-label={`Confirm delete ${d.filename}`}
                        className="rounded px-2 py-1 text-xs font-medium text-red-700 bg-red-50 border border-red-200 hover:bg-red-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400 disabled:opacity-50"
                      >
                        {deleting === d.id ? '…' : 'Yes'}
                      </button>
                      <button
                        type="button"
                        onClick={() => setConfirmDelete(null)}
                        aria-label="Cancel delete"
                        className="rounded px-2 py-1 text-xs font-medium text-anchor-dark/60 bg-gray-50 border border-gray-200 hover:bg-gray-100 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
                      >
                        No
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => setConfirmDelete(d.id)}
                      aria-label={`Delete ${d.filename}`}
                      className="rounded p-1 text-gray-300 opacity-0 group-hover:opacity-100 focus:opacity-100 hover:text-red-500 hover:bg-red-50 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
                    >
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 0 1-2.244 2.077H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 0 0-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 0 1 3.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 0 0-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 0 0-7.5 0" />
                      </svg>
                    </button>
                  )}
                </div>
              </li>
            );
          })}
          {!loadingDocs && docs.length === 0 && (
            <li className="flex flex-col items-center py-12 text-center">
              <svg className="mb-3 h-10 w-10 text-gray-300" fill="none" viewBox="0 0 24 24" strokeWidth={1} stroke="currentColor" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 0 1 4.5 9.75h15A2.25 2.25 0 0 1 21.75 12v.75m-8.69-6.44-2.12-2.12a1.5 1.5 0 0 0-1.061-.44H4.5A2.25 2.25 0 0 0 2.25 6v12a2.25 2.25 0 0 0 2.25 2.25h15A2.25 2.25 0 0 0 21.75 18V9a2.25 2.25 0 0 0-2.25-2.25h-5.379a1.5 1.5 0 0 1-1.06-.44Z" />
              </svg>
              <p className="text-sm font-medium text-anchor-dark/60">No documents yet</p>
              <p className="mt-1 text-xs text-anchor-dark/50">
                Upload your first document above to start building your knowledge base.
              </p>
            </li>
          )}
        </ul>
      </div>
    </div>
  );
}
