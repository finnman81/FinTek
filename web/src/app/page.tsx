'use client';

import { useState } from 'react';
import { chatQuery, submitRating } from '@/lib/api';

const DEFAULT_TENANT = process.env.NEXT_PUBLIC_DEFAULT_TENANT_ID || '';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  /** For assistant messages: the user question that led to this answer (for rating). */
  question?: string;
  /** Set after user submits a 1-5 rating. */
  rating?: number;
};

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [sources, setSources] = useState<Array<{ document: string; page?: string; section?: string }>>([]);
  const [loading, setLoading] = useState(false);
  const [tenantId, setTenantId] = useState(DEFAULT_TENANT);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ratingErrorIndex, setRatingErrorIndex] = useState<number | null>(null);
  const [ratingSavingIndex, setRatingSavingIndex] = useState<number | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!question.trim() || !tenantId) return;
    const userQuestion = question.trim();
    setLoading(true);
    setAnswer('');
    setSources([]);
    setError(null);
    try {
      const res = await chatQuery(tenantId, userQuestion);
      setAnswer(res.answer);
      setSources(res.sources || []);
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: userQuestion },
        { role: 'assistant', content: res.answer, question: userQuestion },
      ]);
      setQuestion('');
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleRate(messageIndex: number, rating: number) {
    const msg = messages[messageIndex];
    if (msg?.role !== 'assistant' || !msg.question || !tenantId) return;
    setRatingErrorIndex(null);
    setRatingSavingIndex(messageIndex);
    try {
      await submitRating(tenantId, msg.question, rating, msg.content);
      setMessages((prev) => {
        const next = [...prev];
        if (next[messageIndex]) next[messageIndex] = { ...next[messageIndex], rating };
        return next;
      });
    } catch {
      setRatingErrorIndex(messageIndex);
    } finally {
      setRatingSavingIndex(null);
    }
  }

  return (
    <div className="min-h-screen bg-anchor-light flex flex-col">
      <div className="flex-1 flex flex-col max-w-2xl w-full mx-auto px-4 py-6">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-anchor-navy tracking-tight">
            Anchorpoint
          </h1>
          <p className="text-sm text-anchor-dark/60 mt-0.5">
            Industrial knowledge assistant for ozone systems, service &amp; repair.
          </p>
        </header>

        <div className="flex-1 rounded-xl bg-white shadow-sm border border-gray-200 p-5 flex flex-col">
          {!tenantId && (
            <div className="mb-4 p-3 bg-anchor-cyan/10 border border-anchor-cyan/30 rounded-lg">
              <label className="block text-sm font-medium text-anchor-navy">
                Tenant ID (required)
              </label>
              <input
                type="text"
                value={tenantId}
                onChange={(e) => setTenantId(e.target.value)}
                placeholder="e.g. tenant UUID"
                className="mt-1 block w-full rounded-lg border border-anchor-cyan/40 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50"
              />
            </div>
          )}

          <div className="flex-1 overflow-y-auto space-y-3 mb-4">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`p-3 rounded-lg text-sm ${
                  m.role === 'user'
                    ? 'bg-anchor-blue/10 text-anchor-navy ml-8 border border-anchor-blue/20'
                    : 'bg-anchor-light text-anchor-dark mr-8 border border-gray-200'
                }`}
              >
                <p className="font-semibold text-xs uppercase tracking-wide mb-1 opacity-60">
                  {m.role === 'user' ? 'You' : 'Anchorpoint'}
                </p>
                <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                {m.role === 'assistant' && m.question !== undefined && (
                  <div className="mt-2 flex items-center gap-2 flex-wrap">
                    {m.rating != null ? (
                      <span className="text-xs text-anchor-dark/70">Rated: {m.rating}/5 · Saved</span>
                    ) : (
                      <>
                        <span className="text-xs text-anchor-dark/60 mr-1">Rate:</span>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            onClick={() => handleRate(i, n)}
                            disabled={ratingSavingIndex === i}
                            className="w-7 h-7 rounded border border-gray-300 bg-white text-sm font-medium text-anchor-navy hover:bg-anchor-cyan/20 hover:border-anchor-cyan/50 focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50 disabled:opacity-50"
                          >
                            {n}
                          </button>
                        ))}
                        {ratingErrorIndex === i && (
                          <span className="text-xs text-red-600">Couldn&apos;t save. Try again.</span>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            ))}
            {loading && (
              <p className="text-anchor-cyan text-sm animate-pulse">Thinking...</p>
            )}
            {error && (
              <p className="text-red-600 text-sm" role="alert">{error}</p>
            )}
          </div>

          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a question..."
              className="flex-1 rounded-lg border border-gray-300 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-anchor-cyan/50 focus:border-anchor-cyan"
              disabled={loading}
            />
            <button
              type="submit"
              disabled={loading || !tenantId}
              className="rounded-lg bg-anchor-blue px-5 py-2 text-sm font-medium text-white hover:bg-anchor-navy transition-colors disabled:opacity-40"
            >
              Send
            </button>
          </form>

          {sources.length > 0 && (
            <details className="mt-4 text-sm text-anchor-dark/60">
              <summary className="cursor-pointer hover:text-anchor-navy transition-colors">
                Sources ({sources.length})
              </summary>
              <ul className="mt-2 list-disc list-inside">
                {sources.map((s, i) => (
                  <li key={i}>
                    {s.document}
                    {s.page ? `, p.${s.page}` : ''}
                    {s.section ? `, ${s.section}` : ''}
                  </li>
                ))}
              </ul>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}
