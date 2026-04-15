import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bot, X, Send, Maximize2, Minimize2, ShoppingCart } from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { getAIUserId } from '../utils/aiTracking';

const API_BASE = 'http://localhost:8000/api/ai';
const WS_BASE = 'ws://localhost:8008';

const SESSION_ID = 'widget_' + Math.random().toString(36).slice(2, 10);

function formatPrice(n) {
  return new Intl.NumberFormat('vi-VN').format(n) + 'đ';
}

function renderMarkdown(text) {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>');
}

export default function AIChatWidget() {
  const { user } = useAuth();
  const userId = getAIUserId(user);
  const [open, setOpen] = useState(false);
  const [minimized, setMinimized] = useState(false);
  const [messages, setMessages] = useState([{
    role: 'assistant',
    content: 'Chào bạn! 👋 Tôi là trợ lý AI. Cần tư vấn sản phẩm gì không?',
    products: [],
  }]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [unread, setUnread] = useState(0);
  const ws = useRef(null);
  const retryRef = useRef(0);
  const endRef = useRef(null);
  const { addToCart } = useCart();
  const navigate = useNavigate();

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (!open) return;
    setUnread(0);
    connectWS();
    return () => ws.current?.close();
  }, [open]);

  const connectWS = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    const socket = new WebSocket(`${WS_BASE}/ws/chat/${SESSION_ID}?user_id=${userId}`);
    socket.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === 'typing') {
        setIsTyping(true);
      } else if (data.type === 'message') {
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'assistant', content: data.message, products: data.products || [] }]);
        if (!open) setUnread(n => n + 1);
      }
    };
    socket.onclose = () => {
      if (retryRef.current < 3) {
        retryRef.current += 1;
        setTimeout(connectWS, 3000 * retryRef.current);
      }
    };
    ws.current = socket;
  }, [open, userId]);

  const send = useCallback(async (text) => {
    const msg = (text || input).trim();
    if (!msg) return;
    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: msg, products: [] }]);

    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ message: msg, user_id: userId }));
      setIsTyping(true);
    } else {
      setIsTyping(true);
      try {
        const r = await axios.post(`${API_BASE}/chat`, { message: msg, session_id: SESSION_ID, user_id: userId });
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'assistant', content: r.data.message, products: r.data.products || [] }]);
      } catch {
        setIsTyping(false);
        setMessages(prev => [...prev, { role: 'assistant', content: '⚠️ Lỗi kết nối.', products: [] }]);
      }
    }
  }, [input, userId]);

  const goFullPage = () => {
    setOpen(false);
    navigate('/ai-chat');
  };

  if (!open) {
    return (
      <button
        onClick={() => { setOpen(true); setUnread(0); }}
        style={{
          position: 'fixed', bottom: 28, right: 28, zIndex: 999,
          width: 58, height: 58, borderRadius: '50%',
          background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))',
          border: 'none', cursor: 'pointer', boxShadow: '0 8px 28px rgba(30,64,175,0.45)',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          transition: 'transform 0.2s',
          animation: 'widgetPulse 3s infinite',
        }}
        onMouseEnter={e => e.currentTarget.style.transform = 'scale(1.1)'}
        onMouseLeave={e => e.currentTarget.style.transform = 'scale(1)'}
        title="Chat tư vấn AI"
      >
        <Bot size={26} color="#fff" />
        {unread > 0 && (
          <span style={{ position: 'absolute', top: -4, right: -4, background: '#ef4444', color: '#fff', fontSize: '0.7rem', fontWeight: 700, width: 20, height: 20, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '2px solid white' }}>
            {unread}
          </span>
        )}
      </button>
    );
  }

  return (
    <div style={{
      position: 'fixed', bottom: 28, right: 28, zIndex: 999,
      width: minimized ? 320 : 380,
      height: minimized ? 56 : 540,
      borderRadius: 18, overflow: 'hidden',
      background: 'var(--color-bg-card)',
      boxShadow: '0 20px 60px rgba(0,0,0,0.18), 0 0 0 1px rgba(30,64,175,0.1)',
      display: 'flex', flexDirection: 'column',
      transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
    }}>

      {/* Widget Header */}
      <div style={{ padding: '12px 16px', background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', display: 'flex', alignItems: 'center', gap: 10, cursor: minimized ? 'pointer' : 'default' }}
        onClick={() => minimized && setMinimized(false)}
      >
        <div style={{ width: 34, height: 34, borderRadius: 10, background: 'rgba(255,255,255,0.2)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <Bot size={18} color="#fff" />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: '#fff', fontWeight: 600, fontSize: '0.88rem' }}>AI Tư Vấn Mua Sắm</div>
          {!minimized && <div style={{ color: 'rgba(255,255,255,0.75)', fontSize: '0.72rem' }}>Hỏi tôi về bất kỳ sản phẩm nào</div>}
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <button onClick={goFullPage} title="Mở rộng" style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 7, padding: 6, color: '#fff', cursor: 'pointer', display: 'flex' }}>
            <Maximize2 size={13} />
          </button>
          <button onClick={() => setMinimized(m => !m)} title={minimized ? 'Mở rộng' : 'Thu nhỏ'} style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 7, padding: 6, color: '#fff', cursor: 'pointer', display: 'flex' }}>
            <Minimize2 size={13} />
          </button>
          <button onClick={() => setOpen(false)} title="Đóng" style={{ background: 'rgba(255,255,255,0.15)', border: 'none', borderRadius: 7, padding: 6, color: '#fff', cursor: 'pointer', display: 'flex' }}>
            <X size={13} />
          </button>
        </div>
      </div>

      {!minimized && (
        <>
          {/* Messages */}
          <div style={{ flex: 1, overflowY: 'auto', padding: '14px', display: 'flex', flexDirection: 'column', gap: 12, scrollbarWidth: 'thin' }}>
            {messages.map((msg, i) => (
              <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'flex-end', alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', flexDirection: msg.role === 'user' ? 'row-reverse' : 'row', maxWidth: '90%' }}>
                {msg.role === 'assistant' && (
                  <div style={{ width: 26, height: 26, borderRadius: 8, background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <Bot size={13} color="#fff" />
                  </div>
                )}
                <div>
                  <div style={{
                    padding: '9px 13px', borderRadius: 13, fontSize: '0.83rem', lineHeight: 1.55,
                    background: msg.role === 'user' ? 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))' : 'var(--color-bg-main)',
                    color: msg.role === 'user' ? '#fff' : 'var(--color-text-primary)',
                    borderBottomRightRadius: msg.role === 'user' ? 3 : 13,
                    borderBottomLeftRadius: msg.role === 'user' ? 13 : 3,
                    boxShadow: msg.role === 'user' ? '0 3px 10px rgba(30,64,175,0.25)' : 'var(--shadow-sm)',
                    border: msg.role === 'user' ? 'none' : '1px solid var(--color-border)',
                  }}>
                    {msg.role === 'user'
                      ? msg.content
                      : <span dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }} />}
                  </div>
                  {msg.products && msg.products.slice(0, 2).map(p => p && p.name && (
                    <div key={p.id || p.slug}
                      onClick={() => navigate(`/products/${p.slug}`)}
                      style={{ display: 'flex', gap: 8, padding: '8px', borderRadius: 9, background: '#fff', border: '1px solid var(--color-border)', marginTop: 6, cursor: 'pointer', alignItems: 'center' }}
                    >
                      <img src={p.image_url || `https://picsum.photos/seed/${p.slug}/40/40`} alt={p.name} style={{ width: 36, height: 36, borderRadius: 6, objectFit: 'cover' }} onError={e => { e.target.src = 'https://picsum.photos/seed/p/40/40'; }} />
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <div style={{ fontSize: '0.75rem', fontWeight: 600, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.name}</div>
                        <div style={{ fontSize: '0.75rem', color: 'var(--color-primary)', fontWeight: 700 }}>{formatPrice(p.price)}</div>
                      </div>
                      <button onClick={e => { e.stopPropagation(); addToCart(p, 1); }} style={{ background: 'var(--color-primary)', border: 'none', borderRadius: 6, padding: '4px 7px', color: '#fff', cursor: 'pointer' }}>
                        <ShoppingCart size={11} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
            {isTyping && (
              <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
                <div style={{ width: 26, height: 26, borderRadius: 8, background: 'linear-gradient(135deg,var(--color-primary),var(--color-primary-light))', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Bot size={13} color="#fff" />
                </div>
                <div style={{ background: 'var(--color-bg-main)', border: '1px solid var(--color-border)', borderRadius: 13, borderBottomLeftRadius: 3, padding: '9px 13px', display: 'flex', gap: 4 }}>
                  {[0, 150, 300].map(d => <div key={d} style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--color-primary)', animation: 'aiPulse 1.4s infinite', animationDelay: `${d}ms` }} />)}
                </div>
              </div>
            )}
            <div ref={endRef} />
          </div>

          {/* Quick Chips */}
          <div style={{ padding: '6px 10px', display: 'flex', gap: 5, overflowX: 'auto', scrollbarWidth: 'none', borderTop: '1px solid var(--color-border)' }}>
            {['📱 Điện thoại hot', '💻 Laptop', '⌚ Đồng hồ', '🎧 Tai nghe'].map(q => (
              <button key={q} onClick={() => send(q.replace(/[📱💻⌚🎧] /, ''))}
                style={{ whiteSpace: 'nowrap', border: '1px solid var(--color-border)', background: 'transparent', color: 'var(--color-text-secondary)', borderRadius: 14, padding: '4px 9px', fontSize: '0.72rem', cursor: 'pointer' }}>
                {q}
              </button>
            ))}
          </div>

          {/* Input */}
          <div style={{ padding: '10px 12px', borderTop: '1px solid var(--color-border)' }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', background: 'var(--color-bg-main)', border: '1.5px solid var(--color-border)', borderRadius: 12, padding: '7px 10px' }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') send(); }}
                placeholder="Hỏi về sản phẩm..."
                style={{ flex: 1, border: 'none', background: 'transparent', color: 'var(--color-text-primary)', outline: 'none', fontSize: '0.83rem' }}
              />
              <button onClick={() => send()} disabled={!input.trim() || isTyping}
                style={{ background: input.trim() ? 'var(--color-primary)' : 'var(--color-border)', border: 'none', borderRadius: 8, padding: '5px 9px', color: '#fff', cursor: input.trim() ? 'pointer' : 'default', display: 'flex' }}>
                <Send size={13} />
              </button>
            </div>
          </div>
        </>
      )}

      <style>{`
        @keyframes widgetPulse {
          0%, 100% { box-shadow: 0 8px 28px rgba(30,64,175,0.45); }
          50% { box-shadow: 0 8px 36px rgba(30,64,175,0.65); }
        }
        @keyframes aiPulse {
          0%, 80%, 100% { transform: translateY(0); opacity: 1; }
          40% { transform: translateY(-5px); opacity: 0.5; }
        }
      `}</style>
    </div>
  );
}
