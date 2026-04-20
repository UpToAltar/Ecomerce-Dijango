import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, ShoppingBag, Sparkles, BarChart3, RefreshCw, MessageCircle } from 'lucide-react';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { getAIUserId } from '../utils/aiTracking';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const AI_NEW_API = `${API}/ai-new`;

export default function AINewRecommend() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [tab, setTab] = useState('recommend'); // recommend | chat | stats
  const [recommendations, setRecommendations] = useState([]);
  const [loadingRec, setLoadingRec] = useState(false);
  const [messages, setMessages] = useState([
    { role: 'bot', text: 'Xin chào! Tôi là trợ lý AI mới, được xây dựng bằng RNN/LSTM/BiLSTM + Knowledge Graph + RAG. Hãy hỏi tôi về sản phẩm!' }
  ]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [stats, setStats] = useState(null);
  const [trainStatus, setTrainStatus] = useState(null);
  const chatEndRef = useRef(null);

  const userId = getAIUserId(user);

  useEffect(() => {
    if (tab === 'recommend') fetchRecommendations();
    if (tab === 'stats') fetchStats();
  }, [tab]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const fetchRecommendations = async () => {
    setLoadingRec(true);
    try {
      const res = await axios.get(`${AI_NEW_API}/recommend/${userId}`);
      setRecommendations(res.data.recommended_products || []);
    } catch (e) {
      console.error('Failed to fetch recommendations', e);
    } finally {
      setLoadingRec(false);
    }
  };

  const fetchStats = async () => {
    try {
      const [statsRes, trainRes] = await Promise.all([
        axios.get(`${AI_NEW_API}/stats`).catch(() => ({ data: null })),
        axios.get(`${AI_NEW_API}/train/status`).catch(() => ({ data: null })),
      ]);
      setStats(statsRes.data);
      setTrainStatus(trainRes.data);
    } catch (e) {
      console.error(e);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || sending) return;
    const msg = input.trim();
    setInput('');
    setMessages(prev => [...prev, { role: 'user', text: msg }]);
    setSending(true);

    try {
      const res = await axios.post(`${AI_NEW_API}/chat`, {
        message: msg,
        user_id: userId,
      });
      setMessages(prev => [...prev, { role: 'bot', text: res.data.reply }]);
    } catch (e) {
      setMessages(prev => [...prev, { role: 'bot', text: 'Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại!' }]);
    } finally {
      setSending(false);
    }
  };

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  const tabStyle = (active) => ({
    padding: '12px 24px',
    border: 'none',
    background: active ? 'var(--color-primary)' : 'var(--color-surface-elevated)',
    color: active ? 'white' : 'var(--color-text)',
    borderRadius: '10px 10px 0 0',
    cursor: 'pointer',
    fontWeight: 600,
    fontSize: '0.95rem',
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    transition: 'all 0.2s',
  });

  return (
    <div className="container" style={{ padding: '30px 20px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1 style={{ fontSize: '1.8rem', fontWeight: 800, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '10px' }}>
        <Sparkles size={28} color="var(--color-primary)" />
        AI Recommendation Engine
      </h1>
      <p style={{ color: 'var(--color-text-muted)', marginBottom: '24px', fontSize: '0.9rem' }}>
        Powered by RNN/LSTM/BiLSTM + Neo4j Knowledge Graph + RAG
      </p>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '4px', marginBottom: '0' }}>
        <button style={tabStyle(tab === 'recommend')} onClick={() => setTab('recommend')}>
          <ShoppingBag size={18} /> Gợi ý sản phẩm
        </button>
        <button style={tabStyle(tab === 'chat')} onClick={() => setTab('chat')}>
          <MessageCircle size={18} /> Chat AI (RAG)
        </button>
        <button style={tabStyle(tab === 'stats')} onClick={() => setTab('stats')}>
          <BarChart3 size={18} /> Thống kê & Model
        </button>
      </div>

      <div style={{
        background: 'var(--color-surface-elevated)',
        borderRadius: '0 16px 16px 16px',
        padding: '24px',
        minHeight: '500px',
        border: '1px solid var(--color-border)',
      }}>
        {/* ─── TAB: Recommendations ─── */}
        {tab === 'recommend' && (
          <div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2 style={{ margin: 0, fontSize: '1.3rem' }}>Sản phẩm gợi ý cho bạn</h2>
              <button className="btn btn-outline" onClick={fetchRecommendations} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <RefreshCw size={16} /> Làm mới
              </button>
            </div>
            {loadingRec ? (
              <div style={{ textAlign: 'center', padding: '60px' }}>
                <div className="spinner"></div>
                <p style={{ marginTop: '16px', color: 'var(--color-text-muted)' }}>Đang phân tích hành vi và tạo gợi ý...</p>
              </div>
            ) : recommendations.length > 0 ? (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))', gap: '16px' }}>
                {recommendations.map((p, i) => (
                  <div
                    key={p.id || i}
                    className="product-card"
                    style={{ cursor: p.slug ? 'pointer' : 'default', padding: '16px', borderRadius: '12px', transition: 'transform 0.2s', position: 'relative' }}
                    onClick={() => p.slug && navigate(`/products/${p.slug}`)}
                    onMouseEnter={e => e.currentTarget.style.transform = 'translateY(-4px)'}
                    onMouseLeave={e => e.currentTarget.style.transform = 'translateY(0)'}
                  >
                    {p.discount_percent > 0 && (
                      <span style={{ position: 'absolute', top: '10px', right: '10px', background: '#ef4444', color: 'white', borderRadius: '6px', padding: '2px 8px', fontSize: '0.75rem', fontWeight: 700 }}>
                        -{p.discount_percent}%
                      </span>
                    )}
                    <div style={{ width: '100%', height: '160px', borderRadius: '8px', marginBottom: '10px', background: '#f8f9fa', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                      {p.image_url ? (
                        <img src={p.image_url} alt={p.name} style={{ width: '100%', height: '100%', objectFit: 'contain', padding: '8px' }} />
                      ) : (
                        <ShoppingBag size={40} style={{ opacity: 0.2 }} />
                      )}
                    </div>
                    {p.category_name && <span style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{p.category_name}</span>}
                    <h4 style={{ fontSize: '0.9rem', fontWeight: 600, marginBottom: '4px', lineHeight: 1.3, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{p.name || `Product ${p.id}`}</h4>
                    {p.brand && <p style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)', margin: '0 0 6px' }}>{p.brand}</p>}
                    <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                      {p.price ? <span style={{ fontSize: '1.05rem', fontWeight: 700, color: 'var(--color-primary)' }}>{formatPrice(p.price)}</span> : null}
                      {p.compare_price && Number(p.compare_price) > Number(p.price) && (
                        <span style={{ fontSize: '0.75rem', textDecoration: 'line-through', color: 'var(--color-text-muted)' }}>{formatPrice(p.compare_price)}</span>
                      )}
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '6px' }}>
                      {p.rating_avg > 0 && <span style={{ fontSize: '0.75rem', color: '#f59e0b' }}>{'★'.repeat(Math.round(Number(p.rating_avg)))} {Number(p.rating_avg).toFixed(1)}</span>}
                      {p.stock_quantity > 0 ? (
                        <span style={{ fontSize: '0.7rem', color: '#10b981' }}>Còn hàng</span>
                      ) : (
                        <span style={{ fontSize: '0.7rem', color: '#ef4444' }}>Hết hàng</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ textAlign: 'center', padding: '60px', color: 'var(--color-text-muted)' }}>
                <ShoppingBag size={48} style={{ marginBottom: '12px', opacity: 0.3 }} />
                <p>Chưa có gợi ý. Hãy xem thêm sản phẩm để hệ thống học hành vi của bạn!</p>
              </div>
            )}
          </div>
        )}

        {/* ─── TAB: Chat ─── */}
        {tab === 'chat' && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '500px' }}>
            <div style={{ flex: 1, overflowY: 'auto', padding: '12px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {messages.map((m, i) => (
                <div key={i} style={{
                  display: 'flex',
                  justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start',
                  gap: '8px',
                }}>
                  {m.role === 'bot' && (
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <Bot size={18} color="white" />
                    </div>
                  )}
                  <div style={{
                    maxWidth: '70%',
                    padding: '12px 16px',
                    borderRadius: m.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                    background: m.role === 'user' ? 'var(--color-primary)' : 'var(--color-surface)',
                    color: m.role === 'user' ? 'white' : 'var(--color-text)',
                    fontSize: '0.9rem',
                    lineHeight: 1.5,
                    whiteSpace: 'pre-wrap',
                  }}>
                    {m.text}
                  </div>
                  {m.role === 'user' && (
                    <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#6366f1', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                      <User size={18} color="white" />
                    </div>
                  )}
                </div>
              ))}
              {sending && (
                <div style={{ display: 'flex', gap: '8px' }}>
                  <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--color-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <Bot size={18} color="white" />
                  </div>
                  <div style={{ padding: '12px 16px', borderRadius: '16px', background: 'var(--color-surface)', color: 'var(--color-text-muted)' }}>
                    Đang suy nghĩ...
                  </div>
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            <div style={{ display: 'flex', gap: '8px', padding: '12px 0 0' }}>
              <input
                type="text"
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && sendMessage()}
                placeholder="Hỏi về sản phẩm, gợi ý, so sánh..."
                style={{
                  flex: 1, padding: '12px 16px', borderRadius: '12px',
                  border: '1px solid var(--color-border)', outline: 'none',
                  fontSize: '0.9rem', background: 'var(--color-surface)',
                  color: 'var(--color-text)',
                }}
              />
              <button
                className="btn btn-primary"
                onClick={sendMessage}
                disabled={sending || !input.trim()}
                style={{ padding: '12px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                <Send size={18} />
              </button>
            </div>
          </div>
        )}

        {/* ─── TAB: Stats ─── */}
        {tab === 'stats' && (
          <div>
            <h2 style={{ margin: '0 0 20px', fontSize: '1.3rem' }}>Thống kê & Trạng thái Model</h2>

            {stats && (
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
                <div className="product-card" style={{ padding: '20px', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)', margin: 0 }}>{stats.total_records?.toLocaleString()}</p>
                  <p style={{ color: 'var(--color-text-muted)', margin: '4px 0 0', fontSize: '0.85rem' }}>Tổng behavior records</p>
                </div>
                <div className="product-card" style={{ padding: '20px', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: '#10b981', margin: 0 }}>{stats.unique_users?.toLocaleString()}</p>
                  <p style={{ color: 'var(--color-text-muted)', margin: '4px 0 0', fontSize: '0.85rem' }}>Unique Users</p>
                </div>
                <div className="product-card" style={{ padding: '20px', textAlign: 'center' }}>
                  <p style={{ fontSize: '2rem', fontWeight: 800, color: '#f59e0b', margin: 0 }}>{Object.keys(stats.action_distribution || {}).length}</p>
                  <p style={{ color: 'var(--color-text-muted)', margin: '4px 0 0', fontSize: '0.85rem' }}>Action Types</p>
                </div>
              </div>
            )}

            {stats?.action_distribution && (
              <div className="product-card" style={{ padding: '20px', marginBottom: '24px' }}>
                <h3 style={{ marginBottom: '16px' }}>Phân bố hành vi</h3>
                <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                  {Object.entries(stats.action_distribution).map(([action, count]) => (
                    <div key={action} style={{
                      padding: '8px 16px', borderRadius: '8px',
                      background: 'var(--color-surface)', border: '1px solid var(--color-border)',
                      display: 'flex', alignItems: 'center', gap: '8px',
                    }}>
                      <span style={{ fontWeight: 600 }}>{action}</span>
                      <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {trainStatus && (
              <div className="product-card" style={{ padding: '20px' }}>
                <h3 style={{ marginBottom: '16px' }}>Model Training Status</h3>
                <p><strong>Status:</strong> <span style={{ color: trainStatus.status === 'completed' ? '#10b981' : '#f59e0b' }}>{trainStatus.status}</span></p>
                {trainStatus.best_model && <p><strong>Best Model:</strong> <span style={{ color: 'var(--color-primary)', fontWeight: 700 }}>{trainStatus.best_model}</span></p>}
                {trainStatus.results && (
                  <div style={{ marginTop: '12px' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '2px solid var(--color-border)' }}>
                          <th style={{ padding: '8px', textAlign: 'left' }}>Model</th>
                          <th style={{ padding: '8px', textAlign: 'right' }}>Accuracy</th>
                          <th style={{ padding: '8px', textAlign: 'right' }}>F1-Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(trainStatus.results).map(([name, r]) => (
                          <tr key={name} style={{ borderBottom: '1px solid var(--color-border)', background: name === trainStatus.best_model ? 'rgba(59,130,246,0.05)' : 'transparent' }}>
                            <td style={{ padding: '8px', fontWeight: name === trainStatus.best_model ? 700 : 400 }}>
                              {name} {name === trainStatus.best_model && '★'}
                            </td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>{(r.accuracy * 100).toFixed(2)}%</td>
                            <td style={{ padding: '8px', textAlign: 'right' }}>{(r.f1 * 100).toFixed(2)}%</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
