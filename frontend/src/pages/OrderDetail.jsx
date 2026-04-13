import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ChevronLeft, Package, MapPin, CreditCard, Clock, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000/api';

export default function OrderDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeLeft, setTimeLeft] = useState(0);

  useEffect(() => {
    const fetchOrder = async () => {
      try {
        const res = await axios.get(`${API}/orders/${id}/`);
        setOrder(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    if (user) {
      fetchOrder();
    }
  }, [id, user]);

  // Expiry countdown for VNPay
  useEffect(() => {
    if (!order?.expires_at || order.status !== 'pending' || order.payment_method !== 'vnpay') return;
    
    const interval = setInterval(() => {
      const remaining = new Date(order.expires_at) - new Date();
      if (remaining <= 0) {
        setTimeLeft(0);
        setOrder(prev => ({ ...prev, status: 'cancelled' }));
        clearInterval(interval);
      } else {
        setTimeLeft(Math.floor(remaining / 1000));
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [order]);

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  if (loading) return <div className="loader-container"><div className="spinner"></div></div>;
  if (!order) return <div className="container" style={{ padding: '60px 20px', textAlign: 'center' }}>Không tìm thấy đơn hàng</div>;

  const addr = order.shipping_address || {};

  return (
    <div className="container" style={{ padding: '40px 20px', maxWidth: '800px' }}>
      <button className="btn btn-outline" onClick={() => navigate('/orders')} style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', border: 'none', paddingLeft: 0 }}>
        <ChevronLeft size={18} /> Quay lại danh sách
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h2 style={{ marginBottom: '8px' }}>Chi tiết đơn hàng #{order.order_number}</h2>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Ngày đặt: {new Date(order.created_at).toLocaleString('vi-VN')}</span>
        </div>
        <div style={{ padding: '8px 16px', borderRadius: '20px', background: 'var(--color-surface-elevated)', fontWeight: 600, textTransform: 'capitalize', border: '1px solid var(--color-border)' }}>
          Trạng thái: {order.status}
        </div>
      </div>

      {order.status === 'pending' && order.payment_method === 'vnpay' && timeLeft > 0 && (
        <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '8px', padding: '16px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px', color: '#b45309' }}>
          <AlertCircle size={24} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: '2px' }}>Chờ thanh toán VNPay</div>
            <div style={{ fontSize: '0.9rem' }}>Đơn hàng sẽ tự động huỷ sau {Math.floor(timeLeft / 60)} phút {timeLeft % 60} giây nếu chưa thanh toán hoàn tất.</div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: '24px', alignItems: 'start' }}>
        {/* Left: Items + Tracking */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>Sản phẩm</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {order.items?.map((item, index) => (
                <div key={index} style={{ display: 'flex', gap: '16px' }}>
                  <img src={item.product_image || `https://picsum.photos/seed/${item.product_id}/80`} style={{ width: '80px', height: '80px', borderRadius: '8px', objectFit: 'cover' }} alt="" />
                  <div style={{ flex: 1 }}>
                    <Link to={`/products/${item.product_id}`} style={{ fontWeight: 600, textDecoration: 'none', color: 'inherit' }}>{item.product_name}</Link>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>Số lượng: {item.quantity}</div>
                    <div style={{ fontWeight: 600, color: 'var(--color-primary)', marginTop: '8px' }}>{formatPrice(item.product_price)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}><Package size={20} /> Giao hàng</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {order.tracking && order.tracking.length > 0 ? (
                order.tracking.map((t, i) => (
                  <div key={i} style={{ display: 'flex', gap: '16px' }}>
                    <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: i===0 ? 'var(--color-primary)' : 'var(--color-border)', marginTop: '4px' }}></div>
                    <div>
                      <div style={{ fontWeight: 600 }}>{t.status}</div>
                      <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{new Date(t.created_at).toLocaleString('vi-VN')} - {t.location}</div>
                      {t.note && <div style={{ fontSize: '0.85rem', marginTop: '4px' }}>{t.note}</div>}
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ color: 'var(--color-text-muted)' }}>Chưa có thông tin vận chuyển.</div>
              )}
            </div>
          </div>
        </div>

        {/* Right: Summary + Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Tổng quan</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              <span>Tạm tính</span>
              <span>{formatPrice(order.total_amount - (order.shipping_fee || 0))}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              <span>Phí vận chuyển</span>
              <span>{formatPrice(order.shipping_fee || 0)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: '16px', fontWeight: 700, fontSize: '1.2rem', color: 'var(--color-primary)' }}>
              <span>Tổng cộng</span>
              <span>{formatPrice(order.total_amount)}</span>
            </div>
          </div>

          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}><MapPin size={18} /> Địa chỉ nhận hàng</h3>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
              <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>{addr.full_name}</div>
              <div>SĐT: {addr.phone}</div>
              <div>{addr.address}</div>
              <div>{addr.city}</div>
            </div>
          </div>

          <div className="product-card" style={{ padding: '24px' }}>
             <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}><CreditCard size={18} /> Thanh toán</h3>
            <div style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              Phương thức: <strong style={{ color: 'var(--color-text)' }}>{order.payment_method === 'vnpay' ? 'VNPay' : 'Thanh toán trực tiếp (COD)'}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
