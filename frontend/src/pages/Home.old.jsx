import React, { useState, useEffect } from 'react';
import { ShoppingCart, Heart, Star, StarHalf, ArrowRight } from 'lucide-react';
import axios from 'axios';
import { useCart } from '../context/CartContext';

export default function Home() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToCart } = useCart();

  const placeholderProducts = [
    {
      id: "1", name: "iPhone 15 Pro Max 256GB", price: 34990000,
      image_url: "https://images.unsplash.com/photo-1695048133142-1a20484d2569?q=80&w=600",
      category_name: "─Éiß╗çn thoß║íi", rating_avg: 4.9, discount_percent: 10
    },
    {
      id: "2", name: "MacBook Pro 14 M3 Pro", price: 49990000,
      image_url: "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?q=80&w=600",
      category_name: "Laptop", rating_avg: 4.8, discount_percent: 5
    },
    {
      id: "3", name: "Sony WH-1000XM5 Wireless", price: 7990000,
      image_url: "https://images.unsplash.com/photo-1618366712010-f4ae9c647dcb?q=80&w=600",
      category_name: "Accessories", rating_avg: 4.7, discount_percent: 15
    },
    {
      id: "4", name: "Minimalist Desk Chair", price: 2490000,
      image_url: "https://images.unsplash.com/photo-1592078615290-033ee584e267?q=80&w=600",
      category_name: "Furniture", rating_avg: 4.5, discount_percent: 0
    }
  ];

  useEffect(() => {
    const fetchProducts = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/products/');
        setProducts(response.data.results || response.data);
      } catch (err) {
        setProducts(placeholderProducts);
      } finally {
        setLoading(false);
      }
    };
    fetchProducts();
  }, []);

  const formatPrice = (price) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);

  return (
    <main className="main-content" style={{ paddingTop: 0 }}>
      {/* Hero Section */}
      <section className="hero">
        <div className="container">
          <div className="hero-content animate-fade-in an-1">
            <h1 className="hero-title" id="hero-title">Redefining Your Tech Lifestyle</h1>
            <p className="hero-subtitle" id="hero-subtitle">
              Discover the latest premium devices and accessories curated for modern living. Unmatched quality, unbeatable style.
            </p>
            <div className="hero-actions">
              <button className="btn btn-primary" id="btn-shop-now">
                Shop Collection <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Featured Products */}
      <section className="container" style={{ marginTop: '40px' }}>
        <div className="section-header animate-fade-in an-2">
          <h2 className="section-title">Latest Arrivals</h2>
        </div>

        {loading ? (
          <div className="loader-container"><div className="spinner"></div></div>
        ) : (
          <div className="product-grid animate-fade-in an-3" id="featured-products-grid">
            {products.map((product) => (
              <article className="product-card" key={product.id}>
                {product.discount_percent > 0 && (
                  <div className="product-badge">-{product.discount_percent}%</div>
                )}
                <div className="product-image-wrap">
                  <img 
                    src={product.image_url || `https://picsum.photos/seed/${product.id}/400/400`} 
                    alt={product.name} 
                    className="product-image"
                  />
                  <div className="product-action-overlay">
                    <button className="btn btn-primary" onClick={() => addToCart(product, 1)} style={{ padding: '8px', flex: 1 }}>
                      <ShoppingCart size={18} style={{ marginRight: '4px' }} /> Add to Cart
                    </button>
                    <button className="btn btn-outline" style={{ padding: '8px', width: '42px', height: '42px', display: 'flex', justifyContent: 'center' }}>
                      <Heart size={18} />
                    </button>
                  </div>
                </div>

                <div className="product-info">
                  <span className="product-category">{product.category_name || 'Category'}</span>
                  <h3 className="product-name">{product.name}</h3>
                  <div className="product-price-row" style={{ marginTop: 'auto', paddingTop: '12px' }}>
                    <span className="price-current">{formatPrice(product.price)}</span>
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
