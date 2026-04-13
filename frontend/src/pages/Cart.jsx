import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Trash2, Plus, Minus, ShoppingBag, ArrowRight } from 'lucide-react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';

export default function Cart() {
  const { cartItems, removeItem, updateQuantity, clearCart, cartTotal } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  if (cartItems.length === 0) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '100px 20px' }}>
        <ShoppingBag size={64} color="var(--color-text-muted)" style={{ margin: '0 auto 24px', opacity: 0.3 }} />
        <h2>Giỏ hàng trống</h2>
        <p style={{ marginTop: '12px', color: 'var(--color-text-secondary)' }}>Bạn chưa thêm sản phẩm nào.</p>
        <Link to="/" className="btn btn-primary" style={{ display: 'inline-flex', marginTop: '24px', gap: '8px', alignItems: 'center' }}>
          Tiếp tục mua sắm <ArrowRight size={16} />
        </Link>
      </div>
    );
  }

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <h2 style={{ marginBottom: '32px' }}>🛒 Giỏ hàng ({cartItems.length} sản phẩm)</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 360px', gap: '32px' }}>
        {/* Cart Items */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {cartItems.map((item) => (
            <div key={item.id} className="product-card" style={{ padding: '16px', display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '16px' }}>
              <div style={{ width: '80px', height: '80px', borderRadius: '8px', overflow: 'hidden', flexShrink: 0, background: 'var(--color-surface-elevated)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                {item.product_image
                  ? <img src={item.product_image} alt={item.product_name} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                  : <ShoppingBag size={32} color="var(--color-text-muted)" />
                }
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h4 style={{ fontSize: '1rem', marginBottom: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {item.product_name || `Sản phẩm ${item.product_id?.split('-')[0]}`}
                </h4>
                <p style={{ fontWeight: 700, color: 'var(--color-primary)' }}>{formatPrice(item.price)}</p>
              </div>
              {/* Qty controls */}
              <div style={{ display: 'flex', alignItems: 'center', border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden' }}>
                <button onClick={() => updateQuantity(item.product_id, item.quantity - 1)} style={{ padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text)' }}><Minus size={14} /></button>
                <span style={{ padding: '8px 12px', fontWeight: 600, minWidth: '36px', textAlign: 'center' }}>{item.quantity}</span>
                <button onClick={() => updateQuantity(item.product_id, item.quantity + 1)} style={{ padding: '8px 12px', background: 'none', border: 'none', cursor: 'pointer', color: 'var(--color-text)' }}><Plus size={14} /></button>
              </div>
              <span style={{ fontWeight: 700, minWidth: '100px', textAlign: 'right' }}>{formatPrice(item.price * item.quantity)}</span>
              <button onClick={() => removeItem(item.product_id)} style={{ padding: '8px', background: 'none', border: 'none', cursor: 'pointer', color: '#ef4444' }}>
                <Trash2 size={18} />
              </button>
            </div>
          ))}
          <button className="btn btn-outline" onClick={clearCart} style={{ alignSelf: 'flex-start', fontSize: '0.85rem' }}>
            Xoá tất cả
          </button>
        </div>

        {/* Summary */}
        <div className="product-card" style={{ padding: '24px', height: 'fit-content', position: 'sticky', top: '100px' }}>
          <h3 style={{ marginBottom: '20px' }}>Tổng đơn hàng</h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px', color: 'var(--color-text-secondary)' }}>
            <span>Tạm tính</span>
            <span>{formatPrice(cartTotal)}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px', color: 'var(--color-text-secondary)' }}>
            <span>Phí vận chuyển</span>
            <span style={{ color: '#16a34a', fontWeight: 600 }}>Miễn phí</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '1.25rem', fontWeight: 800, borderTop: '1px solid var(--color-border)', paddingTop: '20px', marginBottom: '24px' }}>
            <span>Tổng cộng</span>
            <span style={{ color: 'var(--color-primary)' }}>{formatPrice(cartTotal)}</span>
          </div>
          {user ? (
            <button className="btn btn-primary" style={{ width: '100%', height: '48px', fontSize: '1rem', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
              onClick={() => navigate('/checkout')}>
              Đặt hàng <ArrowRight size={18} />
            </button>
          ) : (
            <Link to="/login" className="btn btn-primary" style={{ width: '100%', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}>
              Đăng nhập để đặt hàng
            </Link>
          )}
        </div>
      </div>
    </div>
  );
}
