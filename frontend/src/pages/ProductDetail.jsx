import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ShoppingCart, Star, ChevronLeft, Package, Truck, Shield, Send, User, Trash2 } from 'lucide-react';
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

  // Review states
  const [reviews, setReviews] = useState([]);
  const [reviewStats, setReviewStats] = useState(null);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [newRating, setNewRating] = useState(5);
  const [newComment, setNewComment] = useState('');
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewError, setReviewError] = useState('');
  const [reviewSuccess, setReviewSuccess] = useState('');
  const [hoverRating, setHoverRating] = useState(0);

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

  // Fetch reviews when product is loaded
  useEffect(() => {
    if (!product?.id) return;
    const fetchReviews = async () => {
      setReviewLoading(true);
      try {
        const [reviewsRes, statsRes] = await Promise.all([
          axios.get(`${API}/reviews/?product_id=${product.id}`),
          axios.get(`${API}/reviews/product/${product.id}/stats/`),
        ]);
        setReviews(reviewsRes.data);
        setReviewStats(statsRes.data);
      } catch (err) {
        console.error('Fetch reviews error', err);
      } finally {
        setReviewLoading(false);
      }
    };
    fetchReviews();
  }, [product?.id]);

  const handleSubmitReview = async (e) => {
    e.preventDefault();
    if (!user) {
      setReviewError('Vui lòng đăng nhập để đánh giá sản phẩm.');
      return;
    }
    setReviewError('');
    setReviewSuccess('');
    setReviewSubmitting(true);
    try {
      const res = await axios.post(`${API}/reviews/create/`, {
        product_id: product.id,
        user_id: user.id,
        user_name: `${user.first_name || ''} ${user.last_name || ''}`.trim() || user.email,
        rating: newRating,
        comment: newComment,
      });
      setReviews([res.data, ...reviews]);
      setReviewSuccess('Cảm ơn bạn đã đánh giá!');
      setNewComment('');
      setNewRating(5);
      // Refresh stats
      const statsRes = await axios.get(`${API}/reviews/product/${product.id}/stats/`);
      setReviewStats(statsRes.data);
    } catch (err) {
      setReviewError(err.response?.data?.error || 'Có lỗi xảy ra khi gửi đánh giá.');
    } finally {
      setReviewSubmitting(false);
    }
  };

  const handleDeleteReview = async (reviewId) => {
    if (!window.confirm('Bạn có chắc chắn muốn xóa đánh giá này?')) return;
    try {
      await axios.delete(`${API}/reviews/${reviewId}/`);
      setReviews(reviews.filter(r => r.id !== reviewId));
      const statsRes = await axios.get(`${API}/reviews/product/${product.id}/stats/`);
      setReviewStats(statsRes.data);
    } catch (err) {
      alert('Xóa đánh giá thất bại');
    }
  };

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
    trackBehavior(getAIUserId(user), product.id, 'add_to_cart');
  };

  const userAlreadyReviewed = user && reviews.some(r => r.user_id === user.id);

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
                <Star key={i} size={16} fill={i <= Math.round(reviewStats?.rating_avg || product.rating_avg) ? 'gold' : 'transparent'} color={i <= Math.round(reviewStats?.rating_avg || product.rating_avg) ? 'gold' : '#ccc'} />
              ))}
            </div>
            <span style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>
              {Number(reviewStats?.rating_avg || product.rating_avg || 0).toFixed(1)} ({reviewStats?.rating_count || product.rating_count || 0} đánh giá)
            </span>
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
            {product.stock_quantity > 0 ? `Còn ${product.stock_quantity} sản phẩm` : 'Hết hàng'}
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
              {addedMsg ? 'Đã thêm!' : 'Thêm vào giỏ'}
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

      {/* ─── Reviews Section ─── */}
      <div className="product-card" style={{ marginTop: '40px', padding: '28px' }}>
        <h3 style={{ marginBottom: '24px', fontSize: '1.3rem' }}>Đánh giá sản phẩm</h3>

        {/* Stats summary */}
        {reviewStats && (
          <div style={{ display: 'flex', gap: '32px', marginBottom: '28px', padding: '20px', background: 'var(--color-surface-elevated)', borderRadius: '12px' }}>
            <div style={{ textAlign: 'center', minWidth: '120px' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: 800, color: 'var(--color-primary)' }}>
                {Number(reviewStats.rating_avg || 0).toFixed(1)}
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', margin: '4px 0' }}>
                {[1,2,3,4,5].map(i => (
                  <Star key={i} size={14} fill={i <= Math.round(reviewStats.rating_avg) ? 'gold' : 'transparent'} color={i <= Math.round(reviewStats.rating_avg) ? 'gold' : '#ccc'} />
                ))}
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{reviewStats.rating_count} đánh giá</div>
            </div>
            <div style={{ flex: 1 }}>
              {[5,4,3,2,1].map(star => {
                const count = reviewStats.distribution?.[star] || 0;
                const pct = reviewStats.rating_count > 0 ? (count / reviewStats.rating_count) * 100 : 0;
                return (
                  <div key={star} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                    <span style={{ fontSize: '0.8rem', width: '16px', textAlign: 'right', color: 'var(--color-text-muted)' }}>{star}</span>
                    <Star size={12} fill="gold" color="gold" />
                    <div style={{ flex: 1, height: '8px', background: 'var(--color-border)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ height: '100%', width: `${pct}%`, background: '#facc15', borderRadius: '4px', transition: 'width 0.3s' }}></div>
                    </div>
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', width: '28px' }}>{count}</span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Write review form */}
        {user && !userAlreadyReviewed && (
          <form onSubmit={handleSubmitReview} style={{ marginBottom: '28px', padding: '20px', border: '1px solid var(--color-border)', borderRadius: '12px' }}>
            <h4 style={{ marginBottom: '16px', fontSize: '1rem' }}>Viết đánh giá của bạn</h4>
            {/* Star picker */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '12px' }}>
              <span style={{ fontSize: '0.9rem', marginRight: '8px', color: 'var(--color-text-secondary)' }}>Xếp hạng:</span>
              {[1,2,3,4,5].map(i => (
                <Star
                  key={i}
                  size={24}
                  fill={(hoverRating || newRating) >= i ? 'gold' : 'transparent'}
                  color={(hoverRating || newRating) >= i ? 'gold' : '#ccc'}
                  style={{ cursor: 'pointer' }}
                  onMouseEnter={() => setHoverRating(i)}
                  onMouseLeave={() => setHoverRating(0)}
                  onClick={() => setNewRating(i)}
                />
              ))}
              <span style={{ marginLeft: '8px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{newRating}/5</span>
            </div>
            <textarea
              value={newComment}
              onChange={e => setNewComment(e.target.value)}
              placeholder="Chia sẻ trải nghiệm của bạn về sản phẩm này..."
              style={{
                width: '100%', minHeight: '80px', padding: '12px', borderRadius: '8px',
                border: '1px solid var(--color-border)', background: 'var(--color-surface)',
                color: 'var(--color-text)', fontSize: '0.9rem', resize: 'vertical',
                boxSizing: 'border-box',
              }}
            />
            {reviewError && <div style={{ color: '#dc2626', fontSize: '0.85rem', marginTop: '8px' }}>{reviewError}</div>}
            {reviewSuccess && <div style={{ color: '#16a34a', fontSize: '0.85rem', marginTop: '8px' }}>{reviewSuccess}</div>}
            <button
              type="submit"
              className="btn btn-primary"
              disabled={reviewSubmitting}
              style={{ marginTop: '12px', display: 'flex', alignItems: 'center', gap: '8px', padding: '10px 24px' }}
            >
              <Send size={16} />
              {reviewSubmitting ? 'Đang gửi...' : 'Gửi đánh giá'}
            </button>
          </form>
        )}

        {!user && (
          <div style={{ marginBottom: '24px', padding: '16px', background: '#fef3c7', borderRadius: '8px', color: '#b45309', fontSize: '0.9rem' }}>
            Vui lòng <a href="/login" style={{ fontWeight: 600, color: '#b45309' }}>đăng nhập</a> để viết đánh giá.
          </div>
        )}

        {userAlreadyReviewed && (
          <div style={{ marginBottom: '24px', padding: '16px', background: '#dcfce7', borderRadius: '8px', color: '#16a34a', fontSize: '0.9rem' }}>
            Bạn đã đánh giá sản phẩm này. Cảm ơn bạn!
          </div>
        )}

        {/* Review list */}
        {reviewLoading ? (
          <div style={{ textAlign: 'center', padding: '20px', color: 'var(--color-text-muted)' }}>Đang tải đánh giá...</div>
        ) : reviews.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '30px', color: 'var(--color-text-muted)' }}>
            Chưa có đánh giá nào. Hãy là người đầu tiên đánh giá sản phẩm này!
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {reviews.map(review => (
              <div key={review.id} style={{ padding: '16px', border: '1px solid var(--color-border)', borderRadius: '10px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <div style={{
                      width: '36px', height: '36px', borderRadius: '50%',
                      background: 'var(--gradient-primary)', display: 'flex',
                      alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 600, fontSize: '0.85rem',
                    }}>
                      {(review.user_name?.[0] || 'U').toUpperCase()}
                    </div>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.9rem' }}>{review.user_name || 'Người dùng'}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        {new Date(review.created_at).toLocaleDateString('vi-VN')}
                      </div>
                    </div>
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ display: 'flex' }}>
                      {[1,2,3,4,5].map(i => (
                        <Star key={i} size={14} fill={i <= review.rating ? 'gold' : 'transparent'} color={i <= review.rating ? 'gold' : '#ccc'} />
                      ))}
                    </div>
                    {user && review.user_id === user.id && (
                      <button
                        onClick={() => handleDeleteReview(review.id)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#dc2626', padding: '4px', display: 'flex' }}
                        title="Xóa đánh giá"
                      >
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </div>
                {review.comment && (
                  <p style={{ margin: 0, color: 'var(--color-text-secondary)', lineHeight: 1.6, fontSize: '0.9rem' }}>{review.comment}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
