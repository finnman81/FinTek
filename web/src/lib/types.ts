export type SourceItem = {
  document: string;
  page?: string;
  section?: string;
  relevance_score?: number;
};

export type ChatResponse = {
  answer: string;
  sources: SourceItem[];
  model?: string;
  confidence?: number;
};

export type FeedbackResponse = {
  ok: boolean;
};

export type DocumentInfo = {
  id: string;
  filename: string;
  file_type?: string;
  status: string;
  chunk_count: number;
  created_at?: string;
};

export type UploadResponse = {
  document_id: string;
  job_id: string;
};

export type DocumentStatusResponse = {
  document_id: string;
  status: string;
  error_message?: string;
};

export type UsageData = {
  total_queries: number;
  total_tokens: number;
  avg_confidence: number;
  low_confidence_queries: number;
};

export type KnowledgeGap = {
  question: string;
  confidence: number;
};

export type DeleteResponse = {
  status: string;
  document_id: string;
};

export type Message = {
  role: 'user' | 'assistant';
  content: string;
  question?: string;
  sources?: SourceItem[];
  rating?: number;
};
