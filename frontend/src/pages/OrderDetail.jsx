import React, { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { ChevronLeft, Package, MapPin, CreditCard, Clock, AlertCircle, Truck, CheckCircle, Search } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000/api';

const getOrderStatusInfo = (status) => {
  switch(status?.toLowerCase()) {
    case 'pending': return { text: 'Chờ xử lý', color: '#eab308', icon: <Clock size={16} /> };
    case 'confirmed': return { text: 'Đã xác nhận', color: '#3b82f6', icon: <Package size={16} /> };
    case 'paid': return { text: 'Đã thanh toán', color: '#8b5cf6', icon: <CheckCircle size={16} /> };
    case 'shipping': return { text: 'Đang giao', color: '#f59e0b', icon: <Truck size={16} /> };
    case 'delivered': return { text: 'Đã giao', color: '#16a34a', icon: <CheckCircle size={16} /> };
    case 'cancelled': return { text: 'Đã hủy', color: '#dc2626', icon: <AlertCircle size={16} /> };
    default: return { text: status || 'Không rõ', color: '#6b7280', icon: <Clock size={16} /> };
  }
};

export default function OrderDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [timeLeft, setTimeLeft] = useState(0);
  const [shipment, setShipment] = useState(null);
  const [shipmentLoading, setShipmentLoading] = useState(false);

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

  // Fetch shipment from shipping-service
  useEffect(() => {
    if (!order?.id) return;
    const fetchShipment = async () => {
      setShipmentLoading(true);
      try {
        const res = await axios.get(`${API}/shipping/order/${order.id}/`);
        setShipment(res.data);
      } catch (err) {
        // No shipment yet — that's ok
        setShipment(null);
      } finally {
        setShipmentLoading(false);
      }
    };
    fetchShipment();
  }, [order?.id]);

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

  const handleCancelOrder = async () => {
    if (!window.confirm('Ban co chac chan muon huy don hang nay?')) return;
    try {
      await axios.put(`${API}/orders/${order.id}/cancel/`);
      setOrder(prev => ({ ...prev, status: 'cancelled' }));
    } catch (err) {
      alert(err.response?.data?.error || 'Huy don that bai');
    }
  };

  const getPaymentStatusText = (status) => {
    switch(status?.toLowerCase()) {
      case 'pending': return { text: 'Cho thanh toan', color: '#eab308' };
      case 'completed': return { text: 'Da thanh toan', color: '#16a34a' };
      case 'failed': return { text: 'Thanh toan loi', color: '#dc2626' };
      default: return { text: status || 'Khong ro', color: '#6b7280' };
    }
  };

  const getShipmentStatusInfo = (status) => {
    switch(status) {
      case 'pending': return { text: 'Cho xu ly', color: '#eab308', icon: <Clock size={16} /> };
      case 'picked_up': return { text: 'Da lay hang', color: '#3b82f6', icon: <Package size={16} /> };
      case 'in_transit': return { text: 'Dang van chuyen', color: '#8b5cf6', icon: <Truck size={16} /> };
      case 'out_for_delivery': return { text: 'Dang giao hang', color: '#f59e0b', icon: <Truck size={16} /> };
      case 'delivered': return { text: 'Da giao thanh cong', color: '#16a34a', icon: <CheckCircle size={16} /> };
      case 'failed': return { text: 'Giao hang that bai', color: '#dc2626', icon: <AlertCircle size={16} /> };
      case 'returned': return { text: 'Da hoan tra', color: '#6b7280', icon: <Package size={16} /> };
      default: return { text: status || 'Khong ro', color: '#6b7280', icon: <Clock size={16} /> };
    }
  };

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  if (loading) return <div className="loader-container"><div className="spinner"></div></div>;
  if (!order) return <div className="container" style={{ padding: '60px 20px', textAlign: 'center' }}>Khong tim thay don hang</div>;

  const addr = order.shipping_address || {};
  const shipStatus = shipment ? getShipmentStatusInfo(shipment.status) : null;

  return (
    <div className="container" style={{ padding: '40px 20px', maxWidth: '800px' }}>
      <button className="btn btn-outline" onClick={() => navigate('/orders')} style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', border: 'none', paddingLeft: 0 }}>
        <ChevronLeft size={18} /> Quay lai danh sach
      </button>

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '24px' }}>
        <div>
          <h2 style={{ marginBottom: '8px' }}>Chi tiet don hang #{order.order_number}</h2>
          <span style={{ color: 'var(--color-text-secondary)', fontSize: '0.9rem' }}>Ngay dat: {new Date(order.created_at).toLocaleString('vi-VN')}</span>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          {(order.status === 'pending') && (
            <button onClick={handleCancelOrder} className="btn btn-outline" style={{ padding: '8px 16px', color: '#dc2626', borderColor: '#fca5a5' }}>
              Huỷ đơn
            </button>
          )}
          <div style={{ 
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '8px 16px', borderRadius: '20px', background: 'var(--color-surface-elevated)', 
            fontWeight: 600, border: '1px solid var(--color-border)',
            color: getOrderStatusInfo(order.status).color
          }}>
            {getOrderStatusInfo(order.status).icon}
            {getOrderStatusInfo(order.status).text}
          </div>
        </div>
      </div>

      {order.status === 'pending' && order.payment_method === 'vnpay' && timeLeft > 0 && (
        <div style={{ background: '#fef3c7', border: '1px solid #fde68a', borderRadius: '8px', padding: '16px', marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px', color: '#b45309' }}>
          <AlertCircle size={24} />
          <div>
            <div style={{ fontWeight: 600, marginBottom: '2px' }}>Cho thanh toan VNPay</div>
            <div style={{ fontSize: '0.9rem' }}>Don hang se tu dong huy sau {Math.floor(timeLeft / 60)} phut {timeLeft % 60} giay neu chua thanh toan hoan tat.</div>
          </div>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1fr) 300px', gap: '24px', alignItems: 'start' }}>
        {/* Left: Items + Shipping Tracking */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', borderBottom: '1px solid var(--color-border)', paddingBottom: '12px' }}>San pham</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {order.items?.map((item, index) => (
                <div key={index} style={{ display: 'flex', gap: '16px' }}>
                  <img src={item.product_image || `https://picsum.photos/seed/${item.product_id}/80`} style={{ width: '80px', height: '80px', borderRadius: '8px', objectFit: 'cover' }} alt="" />
                  <div style={{ flex: 1 }}>
                    <Link to={`/products/${item.product_id}`} style={{ fontWeight: 600, textDecoration: 'none', color: 'inherit' }}>{item.product_name}</Link>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)', marginTop: '4px' }}>So luong: {item.quantity}</div>
                    <div style={{ fontWeight: 600, color: 'var(--color-primary)', marginTop: '8px' }}>{formatPrice(item.product_price)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Shipping Tracking from shipping-service */}
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Truck size={20} /> Van chuyen
            </h3>

            {shipmentLoading ? (
              <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '16px' }}>Dang tai thong tin van chuyen...</div>
            ) : shipment ? (
              <div>
                {/* Shipment header */}
                <div style={{ 
                  display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', 
                  gap: '16px', marginBottom: '16px', padding: '12px', 
                  background: 'var(--color-surface-elevated)', borderRadius: '8px' 
                }}>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Mã vận đơn</div>
                    <div style={{ fontWeight: 700, fontSize: '0.95rem', fontFamily: 'monospace', wordBreak: 'break-all' }}>{shipment.tracking_number}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>Đơn vị VC</div>
                    <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{shipment.carrier}</div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: shipStatus?.color, fontWeight: 600, fontSize: '0.9rem' }}>
                    {shipStatus?.icon} {shipStatus?.text}
                  </div>
                </div>

                {/* Tracking timeline */}
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
                  {shipment.tracking_events && shipment.tracking_events.length > 0 ? (
                    shipment.tracking_events.map((t, i) => (
                      <div key={t.id || i} style={{ display: 'flex', gap: '16px', position: 'relative', paddingBottom: i < shipment.tracking_events.length - 1 ? '20px' : '0' }}>
                        {/* Timeline line */}
                        {i < shipment.tracking_events.length - 1 && (
                          <div style={{ position: 'absolute', left: '5px', top: '16px', bottom: '0', width: '2px', background: 'var(--color-border)' }}></div>
                        )}
                        <div style={{
                          width: '12px', height: '12px', borderRadius: '50%', flexShrink: 0,
                          background: i === 0 ? 'var(--color-primary)' : 'var(--color-border)',
                          marginTop: '4px', position: 'relative', zIndex: 1,
                        }}></div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{t.status}</div>
                          <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                            {new Date(t.created_at).toLocaleString('vi-VN')}
                            {t.location && ` - ${t.location}`}
                          </div>
                          {t.note && <div style={{ fontSize: '0.85rem', marginTop: '4px', color: 'var(--color-text-secondary)' }}>{t.note}</div>}
                        </div>
                      </div>
                    ))
                  ) : (
                    <div style={{ color: 'var(--color-text-muted)' }}>Chua co su kien van chuyen.</div>
                  )}
                </div>
              </div>
            ) : (
              /* Fallback to order.tracking if no shipment yet */
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
                  <div style={{ color: 'var(--color-text-muted)' }}>Chua co thong tin van chuyen.</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Summary + Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px' }}>Tong quan</h3>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              <span>Tam tinh</span>
              <span>{formatPrice(order.total_amount - (order.shipping_fee || 0))}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
              <span>Phi van chuyen</span>
              <span>{formatPrice(order.shipping_fee || 0)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--color-border)', paddingTop: '16px', fontWeight: 700, fontSize: '1.2rem', color: 'var(--color-primary)' }}>
              <span>Tong cong</span>
              <span>{formatPrice(order.total_amount)}</span>
            </div>
          </div>

          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}><MapPin size={18} /> Dia chi nhan hang</h3>
            <div style={{ fontSize: '0.9rem', lineHeight: 1.6, color: 'var(--color-text-secondary)' }}>
              <div style={{ fontWeight: 600, color: 'var(--color-text)' }}>{addr.full_name}</div>
              <div>SDT: {addr.phone}</div>
              <div>{addr.address}</div>
              <div>{addr.city}</div>
            </div>
          </div>

          <div className="product-card" style={{ padding: '24px' }}>
             <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}><CreditCard size={18} /> Thanh toan</h3>
            <div style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <div>Phuong thuc: <strong style={{ color: 'var(--color-text)' }}>{order.payment_method === 'vnpay' ? 'VNPay' : 'Thanh toan truc tiep (COD)'}</strong></div>
              {order.payment_status && (
                <div>Trang thai: <strong style={{ color: getPaymentStatusText(order.payment_status).color }}>{getPaymentStatusText(order.payment_status).text}</strong></div>
              )}
            </div>
          </div>

          {/* Tracking number search */}
          {shipment && (
            <div className="product-card" style={{ padding: '24px' }}>
              <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1rem' }}><Search size={18} /> Tra cuu van don</h3>
              <div style={{ fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
                Ma van don: <strong style={{ color: 'var(--color-text)', fontFamily: 'monospace' }}>{shipment.tracking_number}</strong>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
