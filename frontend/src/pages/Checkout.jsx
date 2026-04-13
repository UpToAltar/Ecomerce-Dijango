import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CreditCard, Truck, MapPin, User, Phone } from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

const API = 'http://localhost:8000/api';

export default function Checkout() {
  const { cartItems, cartTotal, clearCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState({
    full_name: user ? `${user.first_name || ''} ${user.last_name || ''}`.trim() : '',
    phone: user?.phone || '',
    address: '',
    city: '',
    note: '',
  });
  const [paymentMethod, setPaymentMethod] = useState('cod');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!user) { navigate('/login'); return; }
    if (cartItems.length === 0) { setError('Giỏ hàng trống'); return; }
    setLoading(true);
    setError('');

    try {
      const shippingAddress = {
        full_name: form.full_name,
        phone: form.phone,
        address: form.address,
        city: form.city,
      };

      const orderPayload = {
        user_id: user.id,
        shipping_address: shippingAddress,
        payment_method: paymentMethod,
        note: form.note,
        shipping_fee: 0,
        items: cartItems.map(item => ({
          product_id: item.product_id,
          product_name: item.product_name,
          product_image: item.product_image,
          product_price: item.price,
          quantity: item.quantity,
        })),
      };

      // 1. Create order
      const orderRes = await axios.post(`${API}/orders/create/`, orderPayload);
      const order = orderRes.data;

      if (paymentMethod === 'cod') {
        // 2a. Create COD payment
        await axios.post(`${API}/payments/create/`, {
          order_id: order.id,
          user_id: user.id,
          amount: order.total_amount,
          method: 'cod',
          user_email: user.email,
          order_number: order.order_number,
          items: order.items,
        });
        clearCart();
        navigate(`/orders/${order.id}?success=cod`);
      } else {
        // 2b. Create VNPay payment + redirect
        const vnpRes = await axios.post(`${API}/payments/vnpay/create/`, {
          order_id: order.id,
          user_id: user.id,
          amount: order.total_amount,
          order_number: order.order_number,
          user_email: user.email,
          items: order.items,
        });
        clearCart();
        // Redirect to VNPay sandbox
        window.location.href = vnpRes.data.payment_url;
      }
    } catch (err) {
      console.error('Checkout error:', err);
      setError(err.response?.data?.error || 'Đặt hàng thất bại. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  };

  const inputStyle = {
    width: '100%', padding: '10px 12px', borderRadius: '8px',
    border: '1px solid var(--color-border)', background: 'var(--color-surface)',
    color: 'var(--color-text)', fontSize: '0.95rem', boxSizing: 'border-box',
  };

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <h2 style={{ marginBottom: '32px' }}>Thanh toán</h2>

      <form onSubmit={handleSubmit}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 380px', gap: '32px' }}>
          {/* Left: Shipping info */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            {/* Shipping address */}
            <div className="product-card" style={{ padding: '24px' }}>
              <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <MapPin size={20} /> Địa chỉ giao hàng
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                      <User size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />Họ và tên
                    </label>
                    <input name="full_name" required value={form.full_name} onChange={handleChange} style={inputStyle} />
                  </div>
                  <div style={{ flex: 1 }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>
                      <Phone size={14} style={{ marginRight: '4px', verticalAlign: 'middle' }} />Số điện thoại
                    </label>
                    <input name="phone" required value={form.phone} onChange={handleChange} style={inputStyle} placeholder="0901234567" />
                  </div>
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Địa chỉ</label>
                  <input name="address" required value={form.address} onChange={handleChange} style={inputStyle} placeholder="Số nhà, tên đường..." />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Tỉnh / Thành phố</label>
                  <input name="city" required value={form.city} onChange={handleChange} style={inputStyle} placeholder="Hà Nội, TP.HCM..." />
                </div>
                <div>
                  <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Ghi chú (tuỳ chọn)</label>
                  <textarea name="note" value={form.note} onChange={handleChange} rows={2} style={{ ...inputStyle, resize: 'vertical' }} placeholder="Ghi chú cho người giao hàng..." />
                </div>
              </div>
            </div>

            {/* Payment method */}
            <div className="product-card" style={{ padding: '24px' }}>
              <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <CreditCard size={20} /> Phương thức thanh toán
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[
                  { value: 'cod', label: '💵 Thanh toán khi nhận hàng (COD)', desc: 'Trả tiền mặt khi nhận hàng' },
                  { value: 'vnpay', label: '🏦 Thanh toán qua VNPay', desc: 'ATM, Visa, Mastercard, QR Code' },
                ].map(opt => (
                  <label key={opt.value} style={{ display: 'flex', alignItems: 'flex-start', gap: '12px', padding: '16px', borderRadius: '10px', border: `2px solid ${paymentMethod === opt.value ? 'var(--color-primary)' : 'var(--color-border)'}`, cursor: 'pointer', transition: 'border-color 0.2s' }}>
                    <input type="radio" name="payment" value={opt.value} checked={paymentMethod === opt.value} onChange={() => setPaymentMethod(opt.value)} style={{ marginTop: '2px' }} />
                    <div>
                      <div style={{ fontWeight: 600 }}>{opt.label}</div>
                      <div style={{ fontSize: '0.83rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>{opt.desc}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>
          </div>

          {/* Right: Order summary */}
          <div className="product-card" style={{ padding: '24px', height: 'fit-content', position: 'sticky', top: '100px' }}>
            <h3 style={{ marginBottom: '20px' }}>Tóm tắt đơn hàng</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '20px', maxHeight: '250px', overflowY: 'auto' }}>
              {cartItems.map(item => (
                <div key={item.id} style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.9rem' }}>
                  <span style={{ color: 'var(--color-text-secondary)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', marginRight: '8px' }}>
                    {item.product_name} x{item.quantity}
                  </span>
                  <span style={{ fontWeight: 600, flexShrink: 0 }}>{formatPrice(item.price * item.quantity)}</span>
                </div>
              ))}
            </div>
            <div style={{ borderTop: '1px solid var(--color-border)', paddingTop: '16px', marginBottom: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', color: 'var(--color-text-secondary)' }}>
                <span>Phí vận chuyển</span>
                <span style={{ color: '#16a34a', fontWeight: 600 }}>Miễn phí</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.2rem', fontWeight: 800 }}>
                <span>Tổng</span>
                <span style={{ color: 'var(--color-primary)' }}>{formatPrice(cartTotal)}</span>
              </div>
            </div>

            {error && <div style={{ background: '#fee2e2', borderRadius: '8px', padding: '10px', color: '#dc2626', fontSize: '0.85rem', marginBottom: '12px' }}>{error}</div>}

            <button type="submit" className="btn btn-primary" style={{ width: '100%', height: '48px', fontSize: '1rem' }} disabled={loading}>
              {loading ? 'Đang xử lý...' : paymentMethod === 'vnpay' ? '🏦 Thanh toán VNPay' : '✓ Đặt hàng (COD)'}
            </button>

            <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
              <Truck size={14} /> Giao hàng trong 2-3 ngày làm việc
            </div>
          </div>
        </div>
      </form>
    </div>
  );
}
