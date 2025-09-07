import React, { useEffect, useMemo, useRef, useState } from 'react';
import axios from 'axios';

// Modern, dark-themed chat UI
export default function DocumentChat({ document, onClose }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [enhancedSummary, setEnhancedSummary] = useState(null);
  const [loadingSummary, setLoadingSummary] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const threadRef = useRef(null);
  const inputRef = useRef(null);

  const docId = document?.document_id;

  useEffect(() => {
    if (!docId) return;
    // Warm welcome + fetch context
    setMessages([
      {
        type: 'system',
        content: `You're chatting about "${document.file_name}". Ask questions or request summaries, comparisons, and extractions.`,
        timestamp: new Date(),
      },
    ]);
    fetchSuggestions();
    fetchEnhancedSummary();
  }, [docId]);

  // Focus input on mount and enable ESC to close
  useEffect(() => {
    const t = setTimeout(() => inputRef.current?.focus(), 0);
    const handleKey = (e) => { if (e.key === 'Escape') onClose?.(); };
    window.addEventListener('keydown', handleKey);
    return () => { clearTimeout(t); window.removeEventListener('keydown', handleKey); };
  }, []);

  useEffect(() => {
    // Auto-scroll to bottom on new message
    if (!threadRef.current) return;
    threadRef.current.scrollTo({ top: threadRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, loading]);

  const fetchEnhancedSummary = async () => {
    setLoadingSummary(true);
    try {
      // Primary: enhanced summary endpoint
      const { data } = await axios.get(`/api/v1/documents/${docId}/summary`);
      setEnhancedSummary(data);
    } catch (e) {
      console.warn('Enhanced summary endpoint failed, trying fallback summary API', e?.response?.data || e?.message);
      try {
        // Fallback: existing summary endpoint
        const { data: fallback } = await axios.get(`/api/v1/summary/${docId}`);
        // Normalize to the same shape the UI expects
        setEnhancedSummary({
          document_id: docId,
          enhanced_summary: fallback?.summary || 'No summary available.',
          original_summary: fallback?.summary || '',
          insights: [],
        });
      } catch (e2) {
        console.error('Failed to load any summary', e2?.response?.data || e2?.message);
        setEnhancedSummary(null);
      }
    } finally {
      setLoadingSummary(false);
    }
  };

  const fetchSuggestions = async () => {
    try {
      const { data } = await axios.get(`/api/v1/chat-suggestions/${docId}`);
      setSuggestions(data?.suggestions || []);
    } catch (e) {
      // silent fail with defaults
      setSuggestions([]);
    }
  };

  const conversationHistory = useMemo(() =>
    messages
      .filter(m => m.type === 'user' || m.type === 'ai')
      .slice(-10)
      .map(m => ({
        question: m.type === 'user' ? m.content : '',
        answer: m.type === 'ai' ? m.content : '',
      }))
      .filter(x => x.question || x.answer)
  , [messages]);

  const sendMessage = async (text) => {
    const message = typeof text === 'string' ? text : input;
    if (!message.trim() || loading) return;

    const userMsg = { type: 'user', content: message.trim(), timestamp: new Date() };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    autoResize();
    setLoading(true);

    try {
      const { data } = await axios.post(`/api/v1/documents/${docId}/chat`, {
        document_id: docId,
        question: message.trim(),
        conversation_history: conversationHistory,
      });

      const aiMsg = { type: 'ai', content: data?.answer || 'No answer received.', timestamp: new Date() };
      setMessages(prev => [...prev, aiMsg]);
    } catch (e) {
  const serverDetail = e?.response?.data?.detail || e?.message;
  console.error('chat error', serverDetail);
  setMessages(prev => [...prev, { type: 'error', content: serverDetail ? String(serverDetail) : 'Something went wrong. Please try again.', timestamp: new Date() }]);
    } finally {
      setLoading(false);
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const autoResize = () => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  useEffect(() => { autoResize(); }, [input]);

  const copyToClipboard = async (text) => {
    try { await navigator.clipboard.writeText(text); } catch {}
  };

  return (
    <div
      className="chat-overlay"
      role="dialog"
      aria-modal="true"
      aria-label={`Chat about ${document?.file_name || 'document'}`}
      onClick={(e) => { if (e.target === e.currentTarget) onClose?.(); }}
    >
      <div className="chat-shell">
      <div className="chat-topbar">
        <div className="doc-identity">
          <div className="doc-avatar">📄</div>
          <div className="doc-meta">
            <div className="doc-name" title={document?.file_name}>{document?.file_name || 'Untitled Document'}</div>
            <div className="doc-sub muted">Ready • AI Assistant</div>
          </div>
        </div>
        <div className="topbar-actions">
          <button className="chip" onClick={() => setSidebarOpen(s => !s)}>
            {sidebarOpen ? 'Hide Context' : 'Show Context'}
          </button>
          <button className="btn btn-outline" onClick={onClose}>Close</button>
        </div>
      </div>

  <div className="chat-body">
        {sidebarOpen && (
          <aside className="chat-sidebar">
            <div className="sidebar-section">
              <div className="sidebar-title">AI-Enhanced Summary</div>
              {loadingSummary ? (
                <div className="skeleton">Loading summary…</div>
              ) : enhancedSummary ? (
                <>
                  <p className="sidebar-text">{enhancedSummary.enhanced_summary}</p>
                  {Array.isArray(enhancedSummary.insights) && enhancedSummary.insights.length > 0 && (
                    <div className="sidebar-block">
                      <div className="sidebar-subtitle">Key Insights</div>
                      <ul className="insight-list">
                        {enhancedSummary.insights.map((it, i) => (
                          <li key={i}>• {it}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </>
              ) : (
                <div className="muted">No summary available</div>
              )}
            </div>

            {suggestions.length > 0 && (
              <div className="sidebar-section">
                <div className="sidebar-title">Suggested prompts</div>
                <div className="chip-group">
                  {suggestions.slice(0, 6).map((s, i) => (
                    <button key={i} className="chip" onClick={() => sendMessage(s)}>{s}</button>
                  ))}
                </div>
              </div>
            )}
          </aside>
        )}

  <main className="chat-thread" ref={threadRef}>
          {messages.filter(m => m.type !== 'system').length === 0 && (
            <div className="thread-empty">
              <div className="empty-icon">🤖</div>
              <div className="empty-title">Ask anything about this document</div>
              <div className="chip-group">
                {['Summarize the key points', 'Extract important dates', 'List all entities', 'What are the main risks?'].map((s, i) => (
                  <button key={i} className="chip" onClick={() => sendMessage(s)}>{s}</button>
                ))}
              </div>
            </div>
          )}

          {messages.map((m, idx) => (
            m.type === 'system' ? null : (
              <div className={`msg-row ${m.type}`} key={idx}>
                <div className="msg-avatar">{m.type === 'user' ? '🧑' : m.type === 'ai' ? '🤖' : '⚠️'}</div>
                <div className="msg-bubble">
                  <div className="msg-text">{m.content}</div>
                  <div className="msg-meta">
                    <span>{m.timestamp?.toLocaleTimeString?.() || ''}</span>
                    {m.type !== 'error' && (
                      <button className="msg-action" title="Copy" onClick={() => copyToClipboard(m.content)}>Copy</button>
                    )}
                  </div>
                </div>
              </div>
            )
          ))}

          {loading && (
            <div className="msg-row ai loading">
              <div className="msg-avatar">🤖</div>
              <div className="msg-bubble">
                <div className="typing">
                  <span></span><span></span><span></span>
                </div>
                <div className="muted">Thinking…</div>
              </div>
            </div>
          )}
        </main>
      </div>

      <div className="chat-inputbar">
        <div className="input-wrap">
          <button className="icon-btn" title="Attach">📎</button>
          <textarea
            ref={inputRef}
            className="chat-textarea"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            placeholder="Ask a question… (Shift+Enter for newline)"
            rows={1}
            disabled={loading}
          />
          <button
            className={`btn btn-primary send-btn`}
            onClick={() => sendMessage()}
            disabled={!input.trim() || loading}
            title="Send"
          >
            {loading ? '…' : 'Send'}
          </button>
        </div>
      </div>
      </div>
    </div>
  );
}
