'use client';

import { useRef, useEffect, useState } from 'react';
import { chatQuery, submitRating } from '@/lib/api';
import { useTenant } from '@/lib/tenant-context';

type Message = {
  role: 'user' | 'assistant';
  content: string;
  question?: string;
  sources?: Array<{ document: string; page?: string; section?: string }>;
  rating?: number;
};

const SUGGESTIONS = [
  'What is the pump priming procedure?',
  'How do I troubleshoot ozone output issues?',
  'What safety precautions apply to maintenance?',
];

export default function ChatPage() {
  const { tenantId } = useTenant();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ratingSavingIndex, setRatingSavingIndex] = useState<number | null>(null);
  const [ratingErrorIndex, setRatingErrorIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const q = question.trim();
    if (!q || !tenantId) return;
    send(q);
  }

  async function send(q: string) {
    setLoading(true);
    setError(null);
    setQuestion('');
    setMessages((prev) => [...prev, { role: 'user', content: q }]);
    try {
      const res = await chatQuery(tenantId, q);
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: res.answer,
          question: q,
          sources: res.sources || [],
        },
      ]);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  async function handleRate(idx: number, rating: number) {
    const msg = messages[idx];
    if (msg?.role !== 'assistant' || !msg.question || !tenantId) return;
    setRatingErrorIndex(null);
    setRatingSavingIndex(idx);
    try {
      await submitRating(tenantId, msg.question, rating, msg.content);
      setMessages((prev) => {
        const next = [...prev];
        if (next[idx]) next[idx] = { ...next[idx], rating };
        return next;
      });
    } catch {
      setRatingErrorIndex(idx);
    } finally {
      setRatingSavingIndex(null);
    }
  }

  const hasMessages = messages.length > 0;
  const needsTenant = !tenantId;

  return (
    <div className="flex flex-1 flex-col">
      <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col px-4 py-4 sm:px-6">
        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pb-4">
          {/* Empty state */}
          {!hasMessages && !loading && (
            <div className="flex flex-col items-center justify-center pt-16 sm:pt-24 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-anchor-cyan/10">
                <svg className="h-7 w-7 text-anchor-cyan" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.068-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-anchor-navy">
                Ask your technical documents
              </h2>
              <p className="mt-1 text-sm text-anchor-dark/50 max-w-sm">
                Get instant, cited answers from your manuals, SOPs, and service documentation.
              </p>
              {needsTenant && (
                <p className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-700">
                  Set a Tenant ID in the nav settings to get started.
                </p>
              )}
              {!needsTenant && (
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {SUGGESTIONS.map((s) => (
                    <button
                      key={s}
                      type="button"
                      onClick={() => send(s)}
                      className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-anchor-dark/70 shadow-sm transition-colors hover:border-anchor-cyan hover:text-anchor-navy"
                    >
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Message thread */}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div
                className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                  m.role === 'user'
                    ? 'bg-anchor-blue text-white rounded-br-md'
                    : 'bg-white border border-gray-200 text-anchor-dark shadow-sm rounded-bl-md'
                }`}
              >
                <p className="whitespace-pre-wrap">{m.content}</p>

                {/* Inline source citations */}
                {m.role === 'assistant' && m.sources && m.sources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2">
                    {m.sources.map((s, si) => (
                      <span
                        key={si}
                        className="inline-flex items-center gap-1 rounded-md bg-anchor-cyan/10 px-2 py-0.5 text-xs text-anchor-cyan"
                      >
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                        </svg>
                        {s.document}
                        {s.page ? `, p.${s.page}` : ''}
                        {s.section ? ` · ${s.section}` : ''}
                      </span>
                    ))}
                  </div>
                )}

                {/* Rating widget */}
                {m.role === 'assistant' && m.question !== undefined && (
                  <div className="mt-2 flex items-center gap-1.5 border-t border-gray-100 pt-2">
                    {m.rating != null ? (
                      <span className="text-xs text-anchor-green flex items-center gap-1">
                        <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M9 12.75 11.25 15 15 9.75M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                        </svg>
                        Rated {m.rating}/5
                      </span>
                    ) : (
                      <>
                        <span className="text-xs text-anchor-dark/40 mr-0.5">Rate:</span>
                        {[1, 2, 3, 4, 5].map((n) => (
                          <button
                            key={n}
                            type="button"
                            onClick={() => handleRate(i, n)}
                            disabled={ratingSavingIndex === i}
                            className="h-6 w-6 rounded text-xs font-medium border border-gray-200 bg-white text-anchor-dark/60 transition-colors hover:border-anchor-cyan hover:bg-anchor-cyan/10 hover:text-anchor-navy disabled:opacity-40"
                          >
                            {n}
                          </button>
                        ))}
                        {ratingErrorIndex === i && (
                          <span className="text-xs text-red-500 ml-1">Failed — retry</span>
                        )}
                      </>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="rounded-2xl rounded-bl-md bg-white border border-gray-200 px-4 py-3 shadow-sm">
                <div className="flex items-center gap-1.5">
                  <span className="h-2 w-2 animate-bounce rounded-full bg-anchor-cyan [animation-delay:-0.3s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-anchor-cyan [animation-delay:-0.15s]" />
                  <span className="h-2 w-2 animate-bounce rounded-full bg-anchor-cyan" />
                </div>
              </div>
            </div>
          )}

          {error && (
            <div className="mx-auto max-w-md rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
              <p className="font-medium">Something went wrong</p>
              <p className="mt-0.5 text-red-600/80">{error}</p>
            </div>
          )}
        </div>

        {/* Sticky input bar */}
        <div className="sticky bottom-0 border-t border-gray-200 bg-anchor-light pt-3 pb-2">
          <form onSubmit={handleSubmit} className="flex gap-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={needsTenant ? 'Set a tenant ID first…' : 'Ask a question…'}
              disabled={loading || needsTenant}
              className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm shadow-sm transition-colors placeholder:text-gray-400 focus:border-anchor-cyan focus:outline-none focus:ring-2 focus:ring-anchor-cyan/30 disabled:bg-gray-50 disabled:text-gray-400"
            />
            <button
              type="submit"
              disabled={loading || needsTenant || !question.trim()}
              className="rounded-xl bg-anchor-blue px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-anchor-navy disabled:opacity-40"
            >
              Send
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
