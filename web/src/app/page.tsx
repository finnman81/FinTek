'use client';

import { useRef, useEffect, useState, useCallback } from 'react';
import { chatQuery, chatQueryStream, submitRating } from '@/lib/api';
import { useTenant } from '@/lib/tenant-context';
import StarRating from '@/components/StarRating';
import { toast } from 'sonner';
import type { Message } from '@/lib/types';

const STORAGE_KEY = 'munitor_chat_sessions';
const CHAT_RESET_EVENT = 'munitor:reset-chat';
const LEGACY_STORAGE_KEY = 'munitor_chat_history';

type ChatSession = {
  id: string;
  title: string;
  updatedAt: number;
  messages: Message[];
};

const SUGGESTIONS = [
  'What are common causes of pneumatic errors, and how should technicians troubleshoot them?',
  'How do I troubleshoot ozone output issues?',
  'For the WEDECO SMOevo 810, what ozone and oxygen safety precautions should operators follow before maintenance?',
  'For the WEDECO PDOevo900 (Everlight III), what startup checks are required before enabling ozone generation?',
  'For the Teledyne 460H, what weekly checks should we perform (zero calibration and filter inspection)?',
];

function makeSession(messages: Message[] = []): ChatSession {
  const id = typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : String(Date.now());
  return {
    id,
    title: 'New chat',
    updatedAt: Date.now(),
    messages,
  };
}

function sessionTitle(messages: Message[]): string {
  const firstUser = messages.find((m) => m.role === 'user')?.content?.trim();
  if (!firstUser) return 'New chat';
  return firstUser.length > 48 ? `${firstUser.slice(0, 48)}...` : firstUser;
}

function loadSessions(): ChatSession[] {
  if (typeof window === 'undefined') return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed as ChatSession[];
  } catch {
    return [];
  }
}

function saveSessions(sessions: ChatSession[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  } catch { /* quota exceeded — silently drop */ }
}

export default function ChatPage() {
  const { tenantId } = useTenant();
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ratingSavingIndex, setRatingSavingIndex] = useState<number | null>(null);
  const [ratingErrorIndex, setRatingErrorIndex] = useState<number | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [hydrated, setHydrated] = useState(false);
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [activeSessionId, setActiveSessionId] = useState('');

  useEffect(() => {
    const loaded = loadSessions();
    if (loaded.length > 0) {
      const sorted = [...loaded].sort((a, b) => b.updatedAt - a.updatedAt);
      setSessions(sorted);
      setActiveSessionId(sorted[0].id);
      setMessages(sorted[0].messages || []);
    } else {
      const fresh = makeSession();
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      setMessages([]);
    }
    setHydrated(true);
  }, []);

  useEffect(() => {
    if (!hydrated || !activeSessionId) return;
    setSessions((prev) => {
      const next = prev.map((s) => {
        if (s.id !== activeSessionId) return s;
        return {
          ...s,
          messages: messages.slice(-100),
          title: sessionTitle(messages),
          updatedAt: Date.now(),
        };
      }).sort((a, b) => b.updatedAt - a.updatedAt);
      return next;
    });
  }, [messages, hydrated, activeSessionId]);

  useEffect(() => {
    if (hydrated) saveSessions(sessions);
  }, [sessions, hydrated]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  useEffect(() => {
    if (!loading) inputRef.current?.focus();
  }, [loading]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    toast.success('Chat history cleared');
  }, []);

  const startNewChat = useCallback(() => {
    const fresh = makeSession();
    setSessions((prev) => [fresh, ...prev]);
    setActiveSessionId(fresh.id);
    setMessages([]);
    setQuestion('');
    setError(null);
  }, []);

  const openSession = useCallback((sessionId: string) => {
    const selected = sessions.find((s) => s.id === sessionId);
    if (!selected) return;
    setActiveSessionId(sessionId);
    setMessages(selected.messages || []);
    setQuestion('');
    setError(null);
  }, [sessions]);

  const deleteSession = useCallback((sessionId: string) => {
    setSessions((prev) => {
      const remaining = prev.filter((s) => s.id !== sessionId);
      if (remaining.length > 0) {
        if (activeSessionId === sessionId) {
          setActiveSessionId(remaining[0].id);
          setMessages(remaining[0].messages || []);
        }
        return remaining;
      }
      const fresh = makeSession();
      setActiveSessionId(fresh.id);
      setMessages([]);
      return [fresh];
    });
  }, [activeSessionId]);

  useEffect(() => {
    const handleChatReset = () => {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(LEGACY_STORAGE_KEY);
      const fresh = makeSession();
      setSessions([fresh]);
      setActiveSessionId(fresh.id);
      setMessages([]);
      setQuestion('');
      setError(null);
    };

    window.addEventListener(CHAT_RESET_EVENT, handleChatReset);
    return () => window.removeEventListener(CHAT_RESET_EVENT, handleChatReset);
  }, []);

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
    const assistantIdx = { current: -1 };
    try {
      setMessages((prev) => {
        assistantIdx.current = prev.length;
        return [...prev, { role: 'assistant', content: '', question: q, sources: [] }];
      });
      const res = await chatQueryStream(tenantId, q, (token) => {
        setMessages((prev) => {
          const next = [...prev];
          const idx = assistantIdx.current;
          if (idx >= 0 && next[idx]) {
            next[idx] = { ...next[idx], content: next[idx].content + token };
          }
          return next;
        });
      });
      setMessages((prev) => {
        const next = [...prev];
        const idx = assistantIdx.current;
        if (idx >= 0 && next[idx]) {
          next[idx] = { ...next[idx], content: res.answer, sources: res.sources || [] };
        }
        return next;
      });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      setError(msg);
      toast.error('Query failed', { description: msg });
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
      toast.success(`Rated ${rating}/5`);
    } catch {
      setRatingErrorIndex(idx);
      toast.error('Could not save rating');
    } finally {
      setRatingSavingIndex(null);
    }
  }

  const hasMessages = messages.length > 0;
  const needsTenant = !tenantId;

  return (
    <div className="flex flex-1 flex-col" role="region" aria-label="Chat">
      <div className="flex w-full flex-1 gap-4 px-4 py-4 sm:px-6">
        <aside className="hidden md:flex md:w-72 md:flex-col rounded-xl border border-gray-200 bg-white p-3 h-[calc(100vh-7.25rem)]">
          <button
            type="button"
            onClick={startNewChat}
            className="mb-3 rounded-lg bg-anchor-blue px-3 py-2 text-sm font-medium text-white hover:bg-anchor-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan"
          >
            + New chat
          </button>
          <div className="flex-1 overflow-y-auto space-y-2">
            {sessions.map((s) => {
              const active = s.id === activeSessionId;
              return (
                <div key={s.id} className={`group flex items-center gap-2 rounded-lg border px-2 py-2 ${active ? 'border-anchor-cyan bg-anchor-cyan/5' : 'border-gray-200 bg-white'}`}>
                  <button
                    type="button"
                    onClick={() => openSession(s.id)}
                    className="min-w-0 flex-1 text-left"
                    title={s.title}
                  >
                    <p className="truncate text-sm font-medium text-anchor-dark">{s.title}</p>
                    <p className="text-xs text-gray-500">
                      {new Date(s.updatedAt).toLocaleString()}
                    </p>
                  </button>
                  <button
                    type="button"
                    onClick={() => deleteSession(s.id)}
                    aria-label="Delete chat session"
                    className="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-red-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" d="m14.74 9-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673A2.25 2.25 0 0 1 15.916 21.75H8.084a2.25 2.25 0 0 1-2.244-2.077L4.772 5.79m14.456 0A48.108 48.108 0 0 0 15.75 5.25m3.478.54a48.11 48.11 0 0 1-3.478-.54m0 0a48.11 48.11 0 0 0-7.5 0m7.5 0V4.5c0-1.068-.845-1.95-1.912-1.997A51.964 51.964 0 0 0 12 2.25c-.636 0-1.27.01-1.902.03C9.03 2.33 8.184 3.214 8.184 4.282V5.25m7.566 0a48.667 48.667 0 0 0-7.566 0" />
                    </svg>
                  </button>
                </div>
              );
            })}
          </div>
        </aside>

        <div className="flex w-full flex-1 flex-col">
        {/* Messages area */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 pb-4" role="log" aria-label="Conversation history" aria-live="polite">
          {/* Empty state */}
          {!hasMessages && !loading && (
            <div className="flex flex-col items-center justify-center pt-16 sm:pt-24 text-center">
              <div className="mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-anchor-cyan/10">
                <svg className="h-7 w-7 text-anchor-cyan" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M7.5 8.25h9m-9 3H12m-9.75 1.51c0 1.6 1.123 2.994 2.707 3.227 1.087.16 2.185.283 3.293.369V21l4.076-4.076a1.526 1.526 0 0 1 1.037-.443 48.282 48.282 0 0 0 5.068-.494c1.584-.233 2.707-1.626 2.707-3.228V6.741c0-1.602-1.123-2.995-2.707-3.228A48.394 48.394 0 0 0 12 3c-2.392 0-4.744.175-7.043.513C3.373 3.746 2.25 5.14 2.25 6.741v6.018Z" />
                </svg>
              </div>
              <h2 className="text-lg font-semibold text-anchor-navy">Ask your technical documents</h2>
              <p className="mt-1 text-sm text-anchor-dark/60 max-w-sm">
                Get instant, cited answers from your manuals, SOPs, and service documentation.
              </p>
              {needsTenant && (
                <p className="mt-4 rounded-lg bg-amber-50 border border-amber-200 px-4 py-2 text-sm text-amber-800" role="alert">
                  Set a Tenant ID in the nav settings to get started.
                </p>
              )}
              {!needsTenant && (
                <div className="mt-6 flex flex-wrap justify-center gap-2" role="group" aria-label="Suggested questions">
                  {SUGGESTIONS.map((s) => (
                    <button key={s} type="button" onClick={() => send(s)} className="rounded-full border border-gray-200 bg-white px-4 py-2 text-sm text-anchor-dark/70 shadow-sm transition-colors hover:border-anchor-cyan hover:text-anchor-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan">
                      {s}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Message thread */}
          {messages.map((m, i) => (
            <div key={i} className={`flex ${m.role === 'user' ? 'justify-end' : 'justify-start'}`} role="article" aria-label={`${m.role === 'user' ? 'You' : 'Munitor AI'} said`}>
              <div className={`max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-3 text-sm leading-relaxed ${m.role === 'user' ? 'bg-anchor-blue text-white rounded-br-md' : 'bg-white border border-gray-200 text-anchor-dark shadow-sm rounded-bl-md'}`}>
                <p className="whitespace-pre-wrap">{m.content}</p>
                {m.role === 'assistant' && m.sources && m.sources.length > 0 && (
                  <div className="mt-3 flex flex-wrap gap-1.5 border-t border-gray-100 pt-2" role="list" aria-label="Sources">
                    {m.sources.map((s, si) => (
                      <span key={si} role="listitem" className="inline-flex items-center gap-1 rounded-md bg-anchor-cyan/10 px-2 py-0.5 text-xs text-anchor-cyan">
                        <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 0 0-3.375-3.375h-1.5A1.125 1.125 0 0 1 13.5 7.125v-1.5a3.375 3.375 0 0 0-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 0 0-9-9Z" />
                        </svg>
                        {s.document}{s.page ? `, p.${s.page}` : ''}{s.section ? ` · ${s.section}` : ''}
                      </span>
                    ))}
                  </div>
                )}
                {m.role === 'assistant' && m.question !== undefined && (
                  <div className="mt-2 border-t border-gray-100 pt-2">
                    <StarRating value={m.rating} onChange={(r) => handleRate(i, r)} disabled={ratingSavingIndex === i} error={ratingErrorIndex === i} />
                  </div>
                )}
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start" role="status" aria-label="Thinking">
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
          <form onSubmit={handleSubmit} className="flex gap-2" role="search" aria-label="Ask a question">
            <label htmlFor="chat-input" className="sr-only">Question</label>
            <input
              id="chat-input"
              ref={inputRef}
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={needsTenant ? 'Set a tenant ID first…' : 'Ask a question…'}
              disabled={loading || needsTenant}
              className="flex-1 rounded-xl border border-gray-300 bg-white px-4 py-2.5 text-sm shadow-sm transition-colors placeholder:text-gray-400 focus:border-anchor-cyan focus:outline-none focus:ring-2 focus:ring-anchor-cyan/30 disabled:bg-gray-50 disabled:text-gray-400"
            />
            <button type="submit" disabled={loading || needsTenant || !question.trim()} aria-label="Send question" className="rounded-xl bg-anchor-blue px-5 py-2.5 text-sm font-medium text-white shadow-sm transition-colors hover:bg-anchor-navy focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan focus-visible:ring-offset-2 disabled:opacity-40">
              Send
            </button>
          </form>
          {hasMessages && (
            <div className="mt-1.5 text-right">
              <button type="button" onClick={clearHistory} className="text-xs text-anchor-dark/30 hover:text-anchor-dark/60 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-anchor-cyan rounded">
                Clear history
              </button>
            </div>
          )}
        </div>
        </div>
      </div>
    </div>
  );
}
