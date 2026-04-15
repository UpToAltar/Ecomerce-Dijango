import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Bot, Send, Sparkles, RefreshCw, ShoppingCart,
  Star, Zap, TrendingUp, MessageSquare, X, ChevronRight, RotateCcw,
} from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { getAIUserId, trackBehavior, forceRebuildKB } from '../utils/aiTracking';

const API_BASE = 'http://localhost:8000/api/ai';
const WS_BASE = 'ws://localhost:8008';

const SESSION_ID = 'chat_' + Math.random().toString(36).slice(2, 10);

const QUICK_TOPICS = [
  { icon: '📱', label: 'Điện thoại mới nhất', msg: 'Điện thoại mới nhất 2024 đang bán?' },
  { icon: '💻', label: 'Laptop dưới 20tr', msg: 'Gợi ý laptop dưới 20 triệu cho sinh viên' },
  { icon: '⌚', label: 'Đồng hồ thông minh', msg: 'So sánh Apple Watch và Samsung Galaxy Watch' },
  { icon: '🎧', label: 'Tai nghe chống ồn', msg: 'Tai nghe chống ồn tốt nhất dưới 5 triệu' },
  { icon: '💄', label: 'Skincare tư vấn', msg: 'Tư vấn routine skincare cho da dầu mụn' },
  { icon: '📦', label: 'Chính sách mua hàng', msg: 'Chính sách đổi trả và giao hàng thế nào?' },
];

function formatPrice(n) {
  if (!n) return '';
  return new Intl.NumberFormat('vi-VN').format(n) + 'đ';
}

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/~~(.+?)~~/g, '<span style="text-decoration:line-through;opacity:0.6">$1</span>')
    .replace(/\n---\n/g, '<hr style="border:none;border-top:1px solid var(--color-border);margin:10px 0"/>')
    .replace(/\n/g, '<br/>');
}

function ProductCard({ product, onAddToCart }) {
  const navigate = useNavigate();
  const hasDiscount = product.compare_price && product.compare_price > product.price;
  const pct = hasDiscount ? Math.round((product.compare_price - product.price) / product.compare_price * 100) : 0;

  return (
    <div
      onClick={() => navigate(`/products/${product.slug}`)}
      style={{
        display: 'flex', gap: 12, padding: '12px', borderRadius: 10,
        background: 'var(--color-bg-main)', border: '1px solid var(--color-border)',
        cursor: 'pointer', transition: 'all 0.2s',
        marginBottom: 8,
      }}
      onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--color-primary)'; e.currentTarget.style.boxShadow = 'var(--shadow-md)'; }}
      onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--color-border)'; e.currentTarget.style.boxShadow = 'none'; }}
    >
      <img
        src={product.image_url || `https://picsum.photos/seed/${product.slug || 'p'}/60/60`}
        alt={product.name}
        style={{ width: 60, height: 60, borderRadius: 8, objectFit: 'cover', flexShrink: 0 }}
        onError={e => { e.target.src = `https://picsum.photos/seed/placeholder/60/60`; }}
      />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontWeight: 600, fontSize: '0.88rem', color: 'var(--color-text-primary)', marginBottom: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {product.name}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 4 }}>
          <span style={{ fontWeight: 700, color: 'var(--color-primary-dark)', fontSize: '0.9rem' }}>{formatPrice(product.price)}</span>
          {hasDiscount && (
            <span style={{ fontSize: '0.75rem', background: '#fee2e2', color: '#dc2626', borderRadius: 4, padding: '1px 5px', fontWeight: 600 }}>-{pct}%</span>
          )}
        </div>
        {product.rating_avg > 0 && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 3, fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>
            <Star size={11} fill="#f59e0b" color="#f59e0b" />
            {product.rating_avg} ({product.rating_count})
          </div>
        )}
      </div>
      {onAddToCart && (
        <button
          onClick={e => { e.stopPropagation(); onAddToCart(product); }}
          style={{
            background: 'var(--color-primary)', color: '#fff', border: 'none',
            borderRadius: 8, padding: '6px 10px', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 4, fontSize: '0.75rem',
            flexShrink: 0, alignSelf: 'center',
          }}
          title="Thêm vào giỏ"
        >
          <ShoppingCart size={13} />
        </button>
      )}
    </div>
  );
}

function MessageBubble({ msg, onAddToCart }) {
  const isUser = msg.role === 'user';

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', maxWidth: '85%', alignSelf: isUser ? 'flex-end' : 'flex-start', flexDirection: isUser ? 'row-reverse' : 'row' }}>
      {!isUser && (
        <div style={{ width: 32, height: 32, borderRadius: 10, background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Bot size={16} color="#fff" />
        </div>
      )}
      <div>
        <div style={{
          padding: '12px 16px', borderRadius: 16, lineHeight: 1.6, fontSize: '0.9rem',
          background: isUser ? 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))' : 'var(--color-bg-card)',
          color: isUser ? '#fff' : 'var(--color-text-primary)',
          borderBottomRightRadius: isUser ? 4 : 16,
          borderBottomLeftRadius: isUser ? 16 : 4,
          boxShadow: isUser ? '0 4px 14px rgba(30,64,175,0.25)' : 'var(--shadow-sm)',
          border: isUser ? 'none' : '1px solid var(--color-border)',
        }}>
          {isUser
            ? msg.content
            : <span dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />}
        </div>
        {!isUser && msg.products && msg.products.length > 0 && (
          <div style={{ marginTop: 8, maxWidth: 380 }}>
            {msg.products.slice(0, 4).map(p => p && p.name && (
              <ProductCard key={p.id || p.slug} product={p} onAddToCart={onAddToCart} />
            ))}
          </div>
        )}
        <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', marginTop: 4, textAlign: isUser ? 'right' : 'left' }}>
          {msg.time}
        </div>
      </div>
    </div>
  );
}

export default function AIChat() {
  const { user } = useAuth();
  const userId = getAIUserId(user);
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: 'Xin chào! 👋 Tôi là trợ lý tư vấn AI.\n\nTôi có thể giúp bạn **tìm kiếm sản phẩm**, **so sánh**, **gợi ý theo ngân sách** và giải đáp **chính sách mua hàng**.\n\nBạn cần tôi tư vấn gì hôm nay?',
    products: [],
    time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
  }]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [wsStatus, setWsStatus] = useState('connecting');
  const [aiStatus, setAiStatus] = useState({ kb_ready: false, model_ready: false, total_products: 0 });
  const [recommendations, setRecommendations] = useState([]);
  const [recSource, setRecSource] = useState('');
  const [kbRebuilding, setKbRebuilding] = useState(false);
  const ws = useRef(null);
  const retryRef = useRef(0);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const { addToCart } = useCart();

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => { scrollToBottom(); }, [messages, isTyping]);

  // Poll AI status
  useEffect(() => {
    const poll = async () => {
      try {
        const r = await axios.get('http://localhost:8008/health');
        setAiStatus(r.data);
      } catch {}
    };
    poll();
    const id = setInterval(poll, 15000);
    return () => clearInterval(id);
  }, []);

  // Fetch recommendations using real user ID
  useEffect(() => {
    const fetchRecs = async () => {
      try {
        const r = await axios.get(`http://localhost:8000/api/ai/recommend/${userId}?top_k=4`);
        if (r.data.products) {
          setRecommendations(r.data.products);
          setRecSource(r.data.source || '');
        }
      } catch {}
    };
    setTimeout(fetchRecs, 2000);
  }, [userId]);

  // WebSocket setup
  const connectWS = useCallback(() => {
    setWsStatus('connecting');
    const socket = new WebSocket(`${WS_BASE}/ws/chat/${SESSION_ID}?user_id=${userId}`);

    socket.onopen = () => { setWsStatus('connected'); retryRef.current = 0; };
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'typing') {
        setIsTyping(true);
      } else if (data.type === 'message') {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.message,
          products: data.products || [],
          intent: data.intent,
          time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    };
    socket.onclose = () => {
      setWsStatus('disconnected');
      if (retryRef.current < 5) {
        retryRef.current += 1;
        setTimeout(connectWS, 2000 * retryRef.current);
      }
    };
    socket.onerror = () => setWsStatus('disconnected');
    ws.current = socket;
  }, []);

  useEffect(() => {
    connectWS();
    return () => ws.current?.close();
  }, [connectWS]);

  const handleAddToCart = useCallback((product) => {
    addToCart(product, 1);
    axios.post(`http://localhost:8000/api/ai/track`, {
      user_id: userId,
      product_id: product.id,
      event_type: 'add_to_cart',
    }).catch(() => {});
  }, [addToCart, userId]);

  const sendMessage = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg) return;
    setInput('');
    setMessages(prev => [...prev, {
      role: 'user',
      content: msg,
      time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    }]);
    setIsTyping(true);

    if (ws.current?.readyState === WebSocket.OPEN) {
      try {
        ws.current.send(JSON.stringify({ message: msg, user_id: userId }));
      } catch {
        setIsTyping(false);
      }
    } else {
      try {
        const r = await axios.post(`${API_BASE}/chat`, {
          message: msg, session_id: SESSION_ID, user_id: userId,
        });
        setIsTyping(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: r.data.message,
          products: r.data.products || [],
          intent: r.data.intent,
          time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        }]);
      } catch {
        setIsTyping(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: '⚠️ Lỗi kết nối đến AI service. Vui lòng thử lại.',
          products: [],
          time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    }
  }, [input, userId]);

  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: 'Cuộc trò chuyện mới bắt đầu! 🆕 Tôi có thể giúp gì cho bạn?',
      products: [],
      time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    }]);
  };

  const wsColor = { connected: '#22c55e', disconnected: '#ef4444', connecting: '#f59e0b' }[wsStatus];
  const wsLabel = { connected: 'Đã kết nối', disconnected: 'Mất kết nối', connecting: 'Đang kết nối...' }[wsStatus];

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100%' }}>
      <div style={{ flex: 1, display: 'flex', maxWidth: 1280, margin: '0 auto', width: '100%', padding: '16px', gap: 20, overflow: 'hidden' }}>

        {/* ── Left: Chat ─────────────────────────────── */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', background: 'var(--color-bg-card)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden', boxShadow: 'var(--shadow-md)' }}>

          {/* Chat Header */}
          <div style={{ padding: '16px 20px', borderBottom: '1px solid var(--color-border)', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', color: '#fff' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Bot size={24} color="#fff" />
              </div>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1rem' }}>AI Tư Vấn Mua Sắm</div>
                <div style={{ fontSize: '0.78rem', opacity: 0.85 }}>RAG · Deep Learning · {aiStatus.total_products} sản phẩm</div>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 6, background: 'rgba(255,255,255,0.15)', borderRadius: 20, padding: '4px 10px', fontSize: '0.78rem' }}>
                <div style={{ width: 7, height: 7, borderRadius: '50%', background: wsColor, boxShadow: `0 0 6px ${wsColor}` }} />
                {wsLabel}
              </div>
              <button onClick={clearChat} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 8, padding: '6px 10px', color: '#fff', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 5, fontSize: '0.8rem' }}>
                <RefreshCw size={13} /> Xoá
              </button>
            </div>
          </div>

          {/* AI Status Bar */}
          {(!aiStatus.kb_ready || !aiStatus.model_ready) && (
            <div style={{ padding: '8px 20px', background: '#fef3c7', borderBottom: '1px solid #fde68a', fontSize: '0.8rem', color: '#92400e', display: 'flex', alignItems: 'center', gap: 6 }}>
              <Zap size={13} />
              AI đang khởi động: {!aiStatus.kb_ready ? 'Đang xây dựng Knowledge Base...' : 'Đang train model...'} Vui lòng chờ.
            </div>
          )}

          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '20px', display: 'flex', flexDirection: 'column', gap: 16 }}>
            {messages.map((msg, i) => (
              <MessageBubble key={i} msg={msg} onAddToCart={handleAddToCart} />
            ))}
            {isTyping && (
              <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
                <div style={{ width: 32, height: 32, borderRadius: 10, background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={16} color="#fff" />
                </div>
                <div style={{ background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', borderRadius: 16, borderBottomLeftRadius: 4, padding: '12px 16px', display: 'flex', gap: 5 }}>
                  {[0, 200, 400].map(d => (
                    <div key={d} style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--color-primary)', animation: 'aiPulse 1.4s infinite', animationDelay: `${d}ms` }} />
                  ))}
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Topics */}
          <div style={{ padding: '8px 16px', display: 'flex', gap: 6, overflowX: 'auto', borderTop: '1px solid var(--color-border)', scrollbarWidth: 'none' }}>
            {QUICK_TOPICS.map(t => (
              <button key={t.label} onClick={() => sendMessage(t.msg)} style={{ whiteSpace: 'nowrap', border: '1px solid var(--color-primary)', background: 'rgba(30,64,175,0.04)', color: 'var(--color-primary)', borderRadius: 20, padding: '5px 12px', fontSize: '0.78rem', fontWeight: 500, cursor: 'pointer', transition: 'all 0.15s', display: 'flex', alignItems: 'center', gap: 4 }}>
                {t.icon} {t.label}
              </button>
            ))}
          </div>

          {/* Input Area */}
          <div style={{ padding: '12px 16px', borderTop: '1px solid var(--color-border)', background: 'var(--color-bg-card)' }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', background: 'var(--color-bg-main)', border: '2px solid var(--color-border)', borderRadius: 14, padding: '10px 14px', transition: 'border-color 0.2s' }}
              onFocus={() => { }} onBlur={() => { }}
            >
              <textarea
                ref={inputRef}
                value={input}
                onChange={e => { setInput(e.target.value); e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 120) + 'px'; }}
                onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
                onFocus={e => e.target.parentNode.style.borderColor = 'var(--color-primary)'}
                onBlur={e => e.target.parentNode.style.borderColor = 'var(--color-border)'}
                placeholder="Hỏi về sản phẩm, giá cả, tư vấn mua hàng... (Enter để gửi)"
                rows={1}
                style={{ flex: 1, border: 'none', background: 'transparent', color: 'var(--color-text-primary)', resize: 'none', outline: 'none', fontFamily: 'inherit', fontSize: '0.9rem', lineHeight: 1.5, maxHeight: 120, minHeight: 22 }}
              />
              <button
                onClick={() => sendMessage()}
                disabled={!input.trim() || isTyping}
                className="btn btn-primary"
                style={{ padding: '8px 14px', flexShrink: 0, borderRadius: 10, minWidth: 44, height: 40 }}
              >
                <Send size={16} />
              </button>
            </div>
            <div style={{ fontSize: '0.72rem', color: 'var(--color-text-muted)', marginTop: 6, textAlign: 'center' }}>
              Shift+Enter để xuống dòng · Powered by RAG + PyTorch Deep Learning
            </div>
          </div>
        </div>

        {/* ── Right Sidebar ───────────────────────────── */}
        <div style={{ width: 300, display: 'flex', flexDirection: 'column', gap: 16, flexShrink: 0, overflowY: 'auto' }}>

          {/* AI System Status */}
          <div style={{ background: 'var(--color-bg-card)', borderRadius: 12, border: '1px solid var(--color-border)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
            <div style={{ padding: '12px 16px', background: 'linear-gradient(135deg,#1e3a8a,#1e40af)', color: '#fff' }}>
              <div style={{ fontWeight: 600, fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 6 }}>
                <Sparkles size={14} /> Trạng thái hệ thống AI
              </div>
            </div>
            <div style={{ padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
              {[
                { label: 'Knowledge Base', ok: aiStatus.kb_ready, detail: aiStatus.kb_ready ? 'Sẵn sàng' : 'Đang xây dựng...' },
                { label: 'Behavior Model', ok: aiStatus.model_ready, detail: aiStatus.model_ready ? 'Đã train' : 'Chưa train' },
                { label: 'RAG Pipeline', ok: aiStatus.kb_ready, detail: 'ChromaDB + LangChain' },
              ].map(s => (
                <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: '0.82rem', color: 'var(--color-text-secondary)' }}>{s.label}</span>
                  <span style={{ fontSize: '0.78rem', fontWeight: 600, color: s.ok ? '#16a34a' : '#d97706', display: 'flex', alignItems: 'center', gap: 4 }}>
                    <span style={{ width: 7, height: 7, borderRadius: '50%', background: s.ok ? '#22c55e' : '#f59e0b', display: 'inline-block' }} />
                    {s.detail}
                  </span>
                </div>
              ))}
              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 8, display: 'flex', justifyContent: 'space-between', fontSize: '0.82rem' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Sản phẩm</span>
                <span style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{aiStatus.total_products}</span>
              </div>
              <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: 8, display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                <span>User ID</span>
                <span style={{ fontFamily: 'monospace', fontSize: '0.72rem', maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis' }} title={userId}>{userId}</span>
              </div>
              {!aiStatus.kb_ready && (
                <button
                  onClick={async () => {
                    setKbRebuilding(true);
                    await forceRebuildKB();
                    setTimeout(() => setKbRebuilding(false), 3000);
                  }}
                  disabled={kbRebuilding}
                  style={{ marginTop: 4, width: '100%', padding: '7px', background: kbRebuilding ? 'var(--color-border)' : 'var(--color-primary)', color: '#fff', border: 'none', borderRadius: 8, cursor: kbRebuilding ? 'default' : 'pointer', fontSize: '0.8rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6 }}
                >
                  <RotateCcw size={13} style={{ animation: kbRebuilding ? 'spin 1s linear infinite' : 'none' }} />
                  {kbRebuilding ? 'Đang xây dựng lại...' : 'Xây dựng lại KB'}
                </button>
              )}
            </div>
          </div>

          {/* Recommendations */}
          {recommendations.length > 0 && (
            <div style={{ background: 'var(--color-bg-card)', borderRadius: 12, border: '1px solid var(--color-border)', overflow: 'hidden', boxShadow: 'var(--shadow-sm)' }}>
              <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--color-border)' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <TrendingUp size={14} color="var(--color-primary)" />
                  <span style={{ fontWeight: 600, fontSize: '0.88rem' }}>Gợi ý cho bạn</span>
                </div>
                {recSource && (
                  <div style={{ marginTop: 4, fontSize: '0.72rem', color: 'var(--color-text-muted)', display: 'flex', alignItems: 'center', gap: 4 }}>
                    {recSource === 'sequence_model' && <><span style={{ color: '#10b981', fontWeight: 600 }}>●</span> Dựa theo lịch sử xem của bạn</>}
                    {recSource.startsWith('content_based') && <><span style={{ color: '#3b82f6', fontWeight: 600 }}>●</span> {recSource.includes(':') ? `Vì bạn quan tâm: ${recSource.split(':')[1]}` : 'Dựa theo sản phẩm bạn đã xem'}</>}
                    {recSource.startsWith('category:') && <><span style={{ color: '#f59e0b', fontWeight: 600 }}>●</span> Phổ biến trong danh mục bạn quan tâm</>}
                    {recSource === 'popularity' && <><span style={{ color: '#6b7280', fontWeight: 600 }}>●</span> Sản phẩm nổi bật</>}
                  </div>
                )}
              </div>
              <div style={{ padding: 12, display: 'flex', flexDirection: 'column', gap: 8 }}>
                {recommendations.slice(0, 4).map(p => p && (
                  <Link key={p.id || p.slug} to={`/products/${p.slug}`}
                    onClick={() => trackBehavior(userId, String(p.id), 'view_detail')}
                    style={{ display: 'flex', gap: 10, textDecoration: 'none', color: 'inherit', padding: '8px', borderRadius: 8, transition: 'background 0.15s' }}
                    onMouseEnter={e => e.currentTarget.style.background = 'var(--color-bg-main)'}
                    onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
                  >
                    <img src={p.image_url || `https://picsum.photos/seed/${p.slug || 'r'}/40/40`} alt={p.name} style={{ width: 40, height: 40, borderRadius: 6, objectFit: 'cover' }} onError={e => { e.target.src = 'https://picsum.photos/seed/r/40/40'; }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: '0.8rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-primary)', fontWeight: 700 }}>{formatPrice(p.price)}</div>
                    </div>
                    <ChevronRight size={14} color="var(--color-text-muted)" style={{ alignSelf: 'center' }} />
                  </Link>
                ))}
              </div>
            </div>
          )}

          {/* Chat Tips */}
          <div style={{ background: 'linear-gradient(135deg,rgba(30,64,175,0.06),rgba(59,130,246,0.04))', borderRadius: 12, border: '1px solid rgba(30,64,175,0.12)', padding: 16 }}>
            <div style={{ fontWeight: 600, fontSize: '0.85rem', color: 'var(--color-primary)', marginBottom: 10, display: 'flex', alignItems: 'center', gap: 6 }}>
              <MessageSquare size={14} /> Mẹo hỏi AI
            </div>
            {[
              '"iPhone tầm 20 triệu tốt nhất"',
              '"So sánh Sony XM5 và Bose QC45"',
              '"Gợi ý quà tặng dưới 500k"',
              '"Chính sách đổi trả như thế nào?"',
            ].map(tip => (
              <div key={tip} onClick={() => { setInput(tip.replace(/"/g, '')); inputRef.current?.focus(); }}
                style={{ fontSize: '0.78rem', color: 'var(--color-text-secondary)', padding: '5px 0', borderBottom: '1px solid rgba(30,64,175,0.08)', cursor: 'pointer', transition: 'color 0.15s' }}
                onMouseEnter={e => e.currentTarget.style.color = 'var(--color-primary)'}
                onMouseLeave={e => e.currentTarget.style.color = 'var(--color-text-secondary)'}
              >
                {tip}
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        @keyframes aiPulse {
          0%, 80%, 100% { transform: translateY(0); opacity: 1; }
          40% { transform: translateY(-6px); opacity: 0.6; }
        }
        @media (max-width: 900px) {
          .ai-sidebar { display: none !important; }
        }
      `}</style>
    </div>
  );
}
