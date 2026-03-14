import type {
  ChatResponse,
  FeedbackResponse,
  DocumentInfo,
  UploadResponse,
  DocumentStatusResponse,
  UsageData,
  KnowledgeGap,
  DeleteResponse,
} from '@/lib/types';

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

export async function chatQuery(tenantId: string, question: string): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/v1/chat`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question }),
  });
  return handleResponse(res);
}

export async function chatQueryStream(
  tenantId: string,
  question: string,
  onToken: (token: string) => void,
): Promise<ChatResponse> {
  const res = await fetch(`${API_URL}/api/v1/chat/stream`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question }),
  });
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new Error(`API ${res.status}: ${text}`);
  }
  const reader = res.body?.getReader();
  if (!reader) throw new Error('No response body');
  const decoder = new TextDecoder();
  let answer = '';
  let sources: ChatResponse['sources'] = [];
  let model = '';
  let buffer = '';

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';
    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      try {
        const data = JSON.parse(line.slice(6));
        if (data.type === 'token') {
          answer += data.content;
          onToken(data.content);
        } else if (data.type === 'done') {
          sources = data.sources || [];
          model = data.model || '';
        } else if (data.type === 'error') {
          throw new Error(data.message);
        }
      } catch (e) {
        if (e instanceof SyntaxError) continue;
        throw e;
      }
    }
  }
  return { answer, sources, model, confidence: 0 };
}

export async function submitRating(
  tenantId: string,
  question: string,
  rating: number,
  answer?: string,
): Promise<FeedbackResponse> {
  const res = await fetch(`${API_URL}/api/v1/feedback`, {
    method: 'POST',
    headers: headers(tenantId),
    body: JSON.stringify({ question, rating, answer }),
  });
  return handleResponse(res);
}

export async function listDocuments(tenantId: string): Promise<DocumentInfo[]> {
  const res = await fetch(`${API_URL}/api/v1/documents`, { headers: headers(tenantId) });
  return handleResponse(res);
}

export async function uploadDocument(tenantId: string, file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_URL}/api/v1/documents/upload`, {
    method: 'POST',
    headers: { 'X-Tenant-ID': tenantId },
    body: formData,
  });
  return handleResponse(res);
}

export async function deleteDocument(tenantId: string, documentId: string): Promise<DeleteResponse> {
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}`, {
    method: 'DELETE',
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function documentStatus(tenantId: string, documentId: string): Promise<DocumentStatusResponse> {
  const res = await fetch(`${API_URL}/api/v1/documents/${documentId}/status`, {
    headers: headers(tenantId),
  });
  return handleResponse(res);
}

export async function usageStats(tenantId: string): Promise<UsageData> {
  const res = await fetch(`${API_URL}/api/v1/admin/usage`, { headers: headers(tenantId) });
  return handleResponse(res);
}

export async function knowledgeGaps(tenantId: string): Promise<KnowledgeGap[]> {
  const res = await fetch(`${API_URL}/api/v1/admin/knowledge-gaps`, { headers: headers(tenantId) });
  return handleResponse(res);
}
