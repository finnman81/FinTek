const API_BASE = '/api/v1';

function headers(tenantId: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': tenantId,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(body.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

// ── Chat ──

export interface SourceItem {
  document: string;
  page?: string;
  section?: string;
  relevance_score?: number;
}

export interface ChatResult {
  answer: string;
  sources: SourceItem[];
  model: string;
  confidence: number;
}

export async function chatQuery(tenantId: string, question: string): Promise<ChatResult> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question }),
  });
  return handleResponse<ChatResult>(res);
}

// ── Feedback ──

export async function submitRating(
  tenantId: string,
  question: string,
  rating: number,
  answer?: string,
): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_BASE}/feedback`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question, rating, answer }),
  });
  return handleResponse<{ ok: boolean }>(res);
}

// ── Documents ──

export interface DocumentInfo {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  chunk_count: number;
  created_at: string;
}

export async function listDocuments(tenantId: string): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_BASE}/documents`, {
    headers: headers(tenantId),
  });
  return handleResponse<DocumentInfo[]>(res);
}

export async function uploadDocument(
  tenantId: string,
  file: File,
): Promise<{ document_id: string; job_id: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    headers: { 'X-Tenant-ID': tenantId },
    body: formData,
  });
  return handleResponse<{ document_id: string; job_id: string }>(res);
}

export async function documentStatus(
  tenantId: string,
  documentId: string,
): Promise<{ document_id: string; status: string; error_message?: string }> {
  const res = await fetch(`${API_BASE}/documents/${documentId}/status`, {
    headers: headers(tenantId),
  });
  return handleResponse<{ document_id: string; status: string; error_message?: string }>(res);
}

// ── Admin ──

export interface UsageStatsResult {
  total_queries: number;
  total_tokens: number;
  avg_confidence: number;
  low_confidence_queries: number;
}

export async function usageStats(tenantId: string): Promise<UsageStatsResult> {
  const res = await fetch(`${API_BASE}/admin/usage`, {
    headers: headers(tenantId),
  });
  return handleResponse<UsageStatsResult>(res);
}
