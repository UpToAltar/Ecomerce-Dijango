import React, { useState, useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, Heart, Star, Search, SlidersHorizontal, ArrowRight, X } from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { getAIUserId, trackBehavior, behaviorHeaders, trackSearch } from '../utils/aiTracking';

const API = 'http://localhost:8000/api';

export default function Home() {
  const [categories, setCategories] = useState([{id: '', name: 'Tất cả'}]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [ordering, setOrdering] = useState('-created_at');
  const [category, setCategory] = useState('');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [inStock, setInStock] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const { addToCart } = useCart();
  const { user } = useAuth();
  const navigate = useNavigate();
  const wsRef = useRef(null);

  const handleProductClick = (product) => {
    trackBehavior(getAIUserId(user), String(product.id), 'view_detail');
    navigate(`/products/${product.slug}`);
  };

  const handleAddToCart = (product) => {
    addToCart(product, 1);
    trackBehavior(getAIUserId(user), String(product.id), 'add_to_cart');
  };

  // Fetch Categories
  useEffect(() => {
    const fetchCategories = async () => {
      try {
        const res = await axios.get(`${API}/products/categories/`);
        // Map the categories. If results is present (pagination), use it.
        const cats = res.data.results || res.data;
        setCategories([{id: '', name: 'Tất cả'}, ...cats]);
      } catch (err) {
        console.error('Failed to fetch categories', err);
      }
    };
    fetchCategories();
  }, []);

  // Real-time stock WebSocket
  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/stock/');
    ws.onmessage = (evt) => {
      try {
        const data = JSON.parse(evt.data);
        if (data.type === 'stock_update') {
          setProducts(prev => prev.map(p =>
            p.id === data.product_id ? { ...p, stock_quantity: data.stock_quantity } : p
          ));
        }
      } catch (_) {}
    };
    wsRef.current = ws;
    return () => ws.close();
  }, []);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (ordering) params.append('ordering', ordering);
      if (category) params.append('category', category);
      if (minPrice) params.append('min_price', minPrice);
      if (maxPrice) params.append('max_price', maxPrice);
      if (inStock) params.append('in_stock', 'true');

      const userId = getAIUserId(null);
      const res = await axios.get(`${API}/products/?${params}`, {
        headers: behaviorHeaders(userId),
      });
      const data = res.data.results || res.data;
      setProducts(data);
      if (search) {
        trackSearch(userId, search, Array.isArray(data) ? data.length : 0);
      }
    } catch (err) {
      console.warn('Using placeholder products');
      setProducts([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(fetchProducts, 300);
    return () => clearTimeout(timer);
  }, [search, ordering, category, minPrice, maxPrice, inStock]);

  const formatPrice = (p) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(p);

  return (
    <main className="main-content" style={{ paddingTop: 0 }}>
      {/* Hero */}
      <section className="hero">
        <div className="container">
          <div className="hero-content animate-fade-in an-1">
            <h1 className="hero-title" id="hero-title">Redefining Your Tech Lifestyle</h1>
            <p className="hero-subtitle">Discover the latest premium devices and accessories curated for modern living.</p>
            <div className="hero-actions">
              <button className="btn btn-primary" id="btn-shop-now" onClick={() => document.getElementById('products-section').scrollIntoView({ behavior: 'smooth' })}>
                Shop Collection <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Search + Filter */}
      <section id="products-section" className="container" style={{ marginTop: '40px' }}>
        <div style={{ display: 'flex', gap: '12px', marginBottom: '20px', flexWrap: 'wrap', alignItems: 'center' }}>
          <div style={{ flex: 1, minWidth: '200px', position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
            <input
              id="product-search"
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Tìm kiếm sản phẩm..."
              style={{ width: '100%', padding: '10px 12px 10px 40px', borderRadius: '8px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }}
            />
          </div>
          <select
            value={ordering}
            onChange={e => setOrdering(e.target.value)}
            style={{ padding: '10px 12px', borderRadius: '8px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}
          >
            <option value="-created_at">Mới nhất</option>
            <option value="price">Giá tăng dần</option>
            <option value="-price">Giá giảm dần</option>
            <option value="-sold_count">Bán chạy nhất</option>
            <option value="-rating_avg">Đánh giá cao</option>
          </select>
          <button className="btn btn-outline" onClick={() => setShowFilters(!showFilters)} style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <SlidersHorizontal size={18} /> Bộ lọc {showFilters ? <X size={14} /> : null}
          </button>
        </div>

        {/* Filter panel */}
        {showFilters && (
          <div className="product-card" style={{ padding: '20px', marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '16px', alignItems: 'flex-end' }}>
            <div>
              <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Danh mục</label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {categories.map(cat => (
                  <button
                    key={cat.id || 'all'}
                    className={category === (cat.slug || cat.id) ? 'btn btn-primary' : 'btn btn-outline'}
                    style={{ padding: '6px 12px', fontSize: '0.85rem' }}
                    onClick={() => setCategory(cat.slug || cat.id)}
                  >
                    {cat.name}
                  </button>
                ))}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Giá từ</label>
                <input type="number" value={minPrice} onChange={e => setMinPrice(e.target.value)} placeholder="0" style={{ width: '120px', padding: '8px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }} />
              </div>
              <span style={{ marginTop: '20px', color: 'var(--color-text-muted)' }}>—</span>
              <div>
                <label style={{ display: 'block', marginBottom: '6px', fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>Đến</label>
                <input type="number" value={maxPrice} onChange={e => setMaxPrice(e.target.value)} placeholder="∞" style={{ width: '120px', padding: '8px', borderRadius: '6px', border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }} />
              </div>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
              <input type="checkbox" checked={inStock} onChange={e => setInStock(e.target.checked)} />
              <span style={{ fontSize: '0.9rem' }}>Còn hàng</span>
            </label>
          </div>
        )}

        <div className="section-header animate-fade-in an-2" style={{ marginBottom: '24px' }}>
          <h2 className="section-title">
            {search ? `Kết quả tìm kiếm "${search}"` : 'Sản phẩm nổi bật'}
          </h2>
          <span style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>{products.length} sản phẩm</span>
        </div>

        {loading ? (
          <div className="loader-container"><div className="spinner"></div></div>
        ) : products.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--color-text-muted)' }}>
            <Search size={48} style={{ margin: '0 auto 16px', opacity: 0.3 }} />
            <p>Không tìm thấy sản phẩm</p>
          </div>
        ) : (
          <div className="product-grid animate-fade-in an-3" id="featured-products-grid">
            {products.map((product) => (
              <article className="product-card" key={product.id}>
                {product.discount_percent > 0 && (
                  <div className="product-badge">-{product.discount_percent}%</div>
                )}
                <div className="product-image-wrap" onClick={() => handleProductClick(product)} style={{ cursor: 'pointer' }}>
                  <img
                    src={product.image_url || `https://picsum.photos/seed/${product.id}/400/400`}
                    alt={product.name}
                    className="product-image"
                  />
                  <div className="product-action-overlay">
                    <button className="btn btn-primary" onClick={(e) => { e.stopPropagation(); handleAddToCart(product); }} style={{ padding: '8px', flex: 1 }}>
                      <ShoppingCart size={18} style={{ marginRight: '4px' }} /> Thêm vào giỏ
                    </button>
                    <button className="btn btn-outline" style={{ padding: '8px', width: '42px', height: '42px', display: 'flex', justifyContent: 'center' }}>
                      <Heart size={18} />
                    </button>
                  </div>
                </div>
                <div className="product-info">
                  <span className="product-category">{product.category_name || 'Category'}</span>
                  <h3 className="product-name">
                    <Link to={`/products/${product.slug}`} onClick={() => trackBehavior(getAIUserId(user), String(product.id), 'view_detail')} style={{ color: 'inherit', textDecoration: 'none' }}>{product.name}</Link>
                  </h3>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '4px' }}>
                    <Star size={14} fill="gold" color="gold" />
                    <span style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{product.rating_avg || '0'} ({product.rating_count || 0})</span>
                  </div>
                  <div className="product-price-row" style={{ marginTop: 'auto', paddingTop: '12px' }}>
                    <span className="price-current">{formatPrice(product.price)}</span>
                    {product.stock_quantity === 0 && (
                      <span style={{ fontSize: '0.75rem', color: '#ef4444', fontWeight: 600 }}>Hết hàng</span>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </main>
  );
}
