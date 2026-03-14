const API_URL = process.env.NEXT_PUBLIC_API_URL || '';

function headers(tenantId: string): HeadersInit {
  return {
    'Content-Type': 'application/json',
    'X-Tenant-ID': tenantId,
  };
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function chatQuery(
  tenantId: string,
  question: string,
): Promise<{ answer: string; sources: Array<{ document: string; page?: string; section?: string }> }> {
  const res = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question }),
  });
  return handleResponse(res);
}

export async function submitRating(
  tenantId: string,
  question: string,
  rating: number,
  answer?: string,
): Promise<{ ok: boolean }> {
  const res = await fetch(`${API_URL}/api/v1/feedback`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question, rating, answer }),
  });
  return handleResponse(res);
}

export async function listDocuments(
  tenantId: string,
): Promise<Array<{ id: string; filename: string; status: string; chunk_count: number }>> {
  const res = await fetch(`${API_URL}/api/v1/documents`, {
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function uploadDocument(
  tenantId: string,
  file: File,
): Promise<{ document_id: string; job_id: string }> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: 'POST',
    headers: { 'X-Tenant-ID': tenantId },
    body: formData,
  });
  return handleResponse(res);
}

export async function deleteDocument(
  tenantId: string,
  documentId: string,
): Promise<{ status: string; document_id: string }> {
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
    method: 'DELETE',
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function documentStatus(
  tenantId: string,
  documentId: string,
): Promise<{ document_id: string; status: string; error_message?: string }> {
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/status`, {
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function usageStats(
  tenantId: string,
): Promise<{ total_queries: number; total_tokens: number; avg_confidence: number; low_confidence_queries: number }> {
  const res = await fetch(`${API_URL}/api/v1/admin/usage`, {
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function knowledgeGaps(
  tenantId: string,
): Promise<Array<{ question: string; confidence: number }>> {
  const res = await fetch(`${API_URL}/api/v1/admin/knowledge-gaps`, {
    headers: headers(tenantId),
  });
  return handleResponse(res);
}
