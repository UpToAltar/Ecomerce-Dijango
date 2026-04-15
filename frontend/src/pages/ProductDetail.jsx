import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShoppingCart, Star, ChevronLeft, Package, Truck, Shield } from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { getAIUserId, trackBehavior, behaviorHeaders } from '../utils/aiTracking';

const API = 'http://localhost:8000/api';

export default function ProductDetail() {
  const { slug } = useParams();
  const navigate = useNavigate();
  const { addToCart } = useCart();
  const { user } = useAuth();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);
  const [qty, setQty] = useState(1);
  const [activeImg, setActiveImg] = useState(0);
  const [addedMsg, setAddedMsg] = useState(false);

  useEffect(() => {
    const fetch = async () => {
      setLoading(true);
      try {
        const userId = getAIUserId(user);
        const res = await axios.get(`${API}/products/${slug}/`, {
          headers: behaviorHeaders(userId),
        });
        setProduct(res.data);
        trackBehavior(userId, res.data.id, 'view_detail');
      } catch (err) {
        console.error('Product fetch error', err);
      } finally {
        setLoading(false);
      }
    };
    fetch();
  }, [slug, user]);

  if (loading) return <div className="loader-container" style={{ minHeight: '60vh' }}><div className="spinner"></div></div>;
  if (!product) return (
    <div className="container" style={{ padding: '80px 20px', textAlign: 'center' }}>
      <p>Sản phẩm không tồn tại.</p>
      <button className="btn btn-primary" style={{ marginTop: '16px' }} onClick={() => navigate('/')}>Về trang chủ</button>
    </div>
  );

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);
  const images = [product.image_url, ...(product.images || [])].filter(Boolean);
  const specs = product.specifications || {};

  const handleAddToCart = () => {
    addToCart(product, qty);
    setAddedMsg(true);
    setTimeout(() => setAddedMsg(false), 2000);
    // Track add-to-cart for AI recommendations
    trackBehavior(getAIUserId(user), product.id, 'add_to_cart');
  };

  return (
    <div className="container" style={{ padding: '40px 20px' }}>
      <button className="btn btn-outline" onClick={() => navigate(-1)} style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px' }}>
        <ChevronLeft size={18} /> Quay lại
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '48px' }}>
        {/* Gallery */}
        <div>
          <div style={{ borderRadius: '16px', overflow: 'hidden', background: 'var(--color-surface-elevated)', marginBottom: '12px', aspectRatio: '1', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <img
              src={images[activeImg] || `https://picsum.photos/seed/${product.id}/600/600`}
              alt={product.name}
              style={{ width: '100%', height: '100%', objectFit: 'contain', padding: '20px', boxSizing: 'border-box' }}
            />
          </div>
          {images.length > 1 && (
            <div style={{ display: 'flex', gap: '8px', overflow: 'auto' }}>
              {images.map((img, i) => (
                <img
                  key={i}
                  src={img}
                  alt=""
                  onClick={() => setActiveImg(i)}
                  style={{ width: '72px', height: '72px', objectFit: 'cover', borderRadius: '8px', cursor: 'pointer', border: i === activeImg ? '2px solid var(--color-primary)' : '2px solid transparent', flexShrink: 0 }}
                />
              ))}
            </div>
          )}
        </div>

        {/* Info */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <span style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{product.category?.name}</span>
            <h1 style={{ fontSize: '1.8rem', fontWeight: 700, marginTop: '8px', marginBottom: '0' }}>{product.name}</h1>
            {product.brand && <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem', marginTop: '4px' }}>by {product.brand}</p>}
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ display: 'flex' }}>
              {[1,2,3,4,5].map(i => (
                <Star key={i} size={16} fill={i <= Math.round(product.rating_avg) ? 'gold' : 'transparent'} color={i <= Math.round(product.rating_avg) ? 'gold' : '#ccc'} />
              ))}
            </div>
            <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>{product.rating_avg} ({product.rating_count} đánh giá)</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
            <span style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--color-primary)' }}>{formatPrice(product.price)}</span>
            {product.compare_price && (
              <span style={{ fontSize: '1.1rem', textDecoration: 'line-through', color: 'var(--color-text-muted)' }}>{formatPrice(product.compare_price)}</span>
            )}
            {product.discount_percent > 0 && (
              <span style={{ background: '#ef4444', color: 'white', borderRadius: '6px', padding: '2px 8px', fontSize: '0.85rem', fontWeight: 700 }}>-{product.discount_percent}%</span>
            )}
          </div>

          <div style={{ padding: '12px 16px', borderRadius: '10px', background: product.stock_quantity > 0 ? '#dcfce7' : '#fee2e2', color: product.stock_quantity > 0 ? '#16a34a' : '#dc2626', fontWeight: 600, fontSize: '0.9rem' }}>
            {product.stock_quantity > 0 ? `✓ Còn ${product.stock_quantity} sản phẩm` : '✗ Hết hàng'}
          </div>

          <p style={{ color: 'var(--color-text-secondary)', lineHeight: 1.7, margin: 0 }}>{product.description}</p>

          {/* Qty + Add to cart */}
          <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', border: '1px solid var(--color-border)', borderRadius: '8px', overflow: 'hidden' }}>
              <button onClick={() => setQty(q => Math.max(1, q-1))} style={{ padding: '10px 16px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--color-text)' }}>-</button>
              <span style={{ padding: '10px 20px', fontWeight: 600, minWidth: '40px', textAlign: 'center' }}>{qty}</span>
              <button onClick={() => setQty(q => Math.min(product.stock_quantity, q+1))} style={{ padding: '10px 16px', background: 'none', border: 'none', cursor: 'pointer', fontSize: '1.2rem', color: 'var(--color-text)' }}>+</button>
            </div>
            <button
              className="btn btn-primary"
              style={{ flex: 1, height: '46px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px', position: 'relative' }}
              onClick={handleAddToCart}
              disabled={!product.is_in_stock}
            >
              <ShoppingCart size={20} />
              {addedMsg ? '✓ Đã thêm!' : 'Thêm vào giỏ'}
            </button>
          </div>

          {/* Trust badges */}
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {[
              { icon: <Truck size={16} />, text: 'Giao hàng miễn phí' },
              { icon: <Shield size={16} />, text: 'Bảo hành 12 tháng' },
              { icon: <Package size={16} />, text: 'Đổi trả 30 ngày' },
            ].map(b => (
              <div key={b.text} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.8rem', color: 'var(--color-text-muted)', padding: '6px 10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}>
                {b.icon} {b.text}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Specifications */}
      {Object.keys(specs).length > 0 && (
        <div className="product-card" style={{ marginTop: '40px', padding: '28px' }}>
          <h3 style={{ marginBottom: '20px' }}>Thông số kỹ thuật</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <tbody>
              {Object.entries(specs).map(([key, val]) => (
                <tr key={key} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontWeight: 500, width: '35%' }}>{key}</td>
                  <td style={{ padding: '12px 16px' }}>{val}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
