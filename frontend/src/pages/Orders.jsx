import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { Package, Clock, CheckCircle, XCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000/api';

export default function Orders() {
  const { user, loading: authLoading } = useAuth();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('');

  useEffect(() => {
    if (authLoading) return;
    if (!user) {
      setLoading(false);
      return;
    }
    const fetchOrders = async () => {
      setLoading(true);
      try {
        let url = `${API}/orders/?user_id=${user.id}`;
        if (filter) url += `&status=${filter}`;
        const res = await axios.get(url);
        setOrders(res.data);
      } catch (err) {
        console.error('Fetch orders failed', err);
      } finally {
        setLoading(false);
      }
    };
    fetchOrders();
  }, [user, filter, authLoading]);

  const handleCancelOrder = async (orderId) => {
    if (!window.confirm('Bạn có chắc chắn muốn huỷ đơn hàng này?')) return;
    try {
      await axios.put(`${API}/orders/${orderId}/cancel/`);
      setOrders(orders.map(o => o.id === orderId ? { ...o, status: 'cancelled' } : o));
    } catch (err) {
      alert(err.response?.data?.error || 'Huỷ đơn thất bại');
    }
  };

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  const getStatusInfo = (status) => {
    switch(status?.toLowerCase()) {
      case 'pending': return { text: 'Chờ xử lý', color: '#eab308', icon: <Clock size={16} /> };
      case 'confirmed': return { text: 'Đã xác nhận', color: '#3b82f6', icon: <Package size={16} /> };
      case 'completed': return { text: 'Hoàn thành', color: '#16a34a', icon: <CheckCircle size={16} /> };
      case 'cancelled': return { text: 'Đã huỷ', color: '#dc2626', icon: <XCircle size={16} /> };
      default: return { text: status, color: '#6b7280', icon: <Clock size={16} /> };
    }
  };

  const getPaymentStatusText = (status) => {
    switch(status?.toLowerCase()) {
      case 'pending': return { text: 'Chờ thanh toán', color: '#eab308' };
      case 'completed': return { text: 'Đã thanh toán', color: '#16a34a' };
      case 'failed': return { text: 'Thanh toán lỗi', color: '#dc2626' };
      default: return { text: status || 'Không rõ', color: '#6b7280' };
    }
  };

  if (authLoading || loading) return <div className="loader-container"><div className="spinner"></div></div>;

  if (!user) return (
    <div className="container" style={{ padding: '80px 20px', textAlign: 'center' }}>
      <p>Vui lòng đăng nhập để xem đơn hàng</p>
      <Link to="/login" className="btn btn-primary" style={{ marginTop: '16px', display: 'inline-block' }}>Đăng nhập</Link>
    </div>
  );

  return (
    <div className="container" style={{ padding: '40px 20px', maxWidth: '800px' }}>
      <h2 style={{ marginBottom: '24px' }}>Đơn hàng của tôi</h2>
      
      <div style={{ display: 'flex', gap: '8px', marginBottom: '24px', overflowX: 'auto', paddingBottom: '8px' }}>
        {[
          { id: '', label: 'Tất cả' },
          { id: 'pending', label: 'Chờ xử lý' },
          { id: 'confirmed', label: 'Đã xác nhận' },
          { id: 'completed', label: 'Hoàn thành' },
          { id: 'cancelled', label: 'Đã hủy' }
        ].map(st => (
          <button
            key={st.id}
            className={filter === st.id ? 'btn btn-primary' : 'btn btn-outline'}
            style={{ padding: '6px 14px', whiteSpace: 'nowrap', fontSize: '0.9rem' }}
            onClick={() => setFilter(st.id)}
          >
            {st.label}
          </button>
        ))}
      </div>

      {orders.length === 0 ? (
        <div className="product-card" style={{ padding: '40px', textAlign: 'center', color: 'var(--color-text-muted)' }}>
          <Package size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
          <p>Không có đơn hàng nào.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {orders.map(order => {
            const stInfo = getStatusInfo(order.status);
            const pInfo = getPaymentStatusText(order.payment_status);
            return (
              <div key={order.id} className="product-card" style={{ padding: '20px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '16px' }}>
                  <div>
                    <span style={{ fontWeight: 600 }}>Mã đơn: #{order.order_number}</span>
                    <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginLeft: '12px' }}>
                      {new Date(order.created_at).toLocaleDateString('vi-VN')}
                    </span>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: stInfo.color, fontWeight: 600, fontSize: '0.9rem' }}>
                    {stInfo.icon} {stInfo.text}
                  </div>
                </div>
                
                {order.items?.map((item, index) => (
                  <div key={index} style={{ display: 'flex', gap: '12px', marginBottom: '12px' }}>
                    <div style={{ width: '60px', height: '60px', borderRadius: '6px', background: 'var(--color-surface-elevated)', overflow: 'hidden' }}>
                      {item.product_image ? (
                        <img src={item.product_image} alt={item.product_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                      ) : (
                        <Package size={24} style={{ margin: '18px auto', display: 'block', color: 'var(--color-text-muted)' }} />
                      )}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 500 }}>{item.product_name}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>x{item.quantity}</div>
                    </div>
                    <div style={{ fontWeight: 600 }}>{formatPrice(item.product_price * item.quantity)}</div>
                  </div>
                ))}
                
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid var(--color-border)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                    <span style={{ color: 'var(--color-text-secondary)' }}>Tổng tiền: <strong style={{ color: 'var(--color-primary)', fontSize: '1.2rem', marginLeft: '6px' }}>{formatPrice(order.total_amount)}</strong></span>
                    {order.payment_status && (
                      <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                        Thanh toán: <span style={{ color: pInfo.color, fontWeight: 500 }}>{pInfo.text}</span>
                      </span>
                    )}
                  </div>
                  <div style={{ display: 'flex', gap: '8px' }}>
                    {(order.status === 'pending') && (
                      <button onClick={() => handleCancelOrder(order.id)} className="btn btn-outline" style={{ padding: '8px 16px', fontSize: '0.9rem', color: '#dc2626', borderColor: '#fca5a5' }}>
                        Huỷ đơn
                      </button>
                    )}
                    <Link to={`/orders/${order.id}`} className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>
                      Xem chi tiết
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
