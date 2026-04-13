import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, User, LogOut, Package, Menu, X, PackageSearch } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Header() {
  const { user, logout } = useAuth();
  const { cartCount } = useCart();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
    setMobileMenuOpen(false);
  };

  return (
    <header className="header">
      <div className="container header-content">
        {/* Logo */}
        <Link to="/" className="logo">
          <div className="logo-icon"><PackageSearch size={24} color="white" /></div>
          ECommerce
        </Link>
        
        {/* Desktop Navigation */}
        <nav className="nav-links desktop-only">
          <Link to="/" className="nav-link">Sản phẩm</Link>
          {user && <Link to="/orders" className="nav-link">Đơn hàng</Link>}
        </nav>

        {/* Actions */}
        <div className="header-actions desktop-only" style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <Link to="/cart" style={{ position: 'relative', color: 'var(--color-text)', display: 'flex', alignItems: 'center' }}>
            <ShoppingCart size={24} />
            {cartCount > 0 && (
              <span style={{ position: 'absolute', top: '-8px', right: '-12px', background: '#ef4444', color: 'white', fontSize: '0.75rem', fontWeight: 800, padding: '2px 6px', borderRadius: '12px', lineHeight: 1 }}>
                {cartCount}
              </span>
            )}
          </Link>
          
          <div style={{ width: '1px', height: '24px', background: 'var(--color-border)' }}></div>

          {user ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: 'var(--gradient-primary)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'white', fontWeight: 600 }}>
                  {(user.first_name?.[0] || user.email?.[0] || 'U').toUpperCase()}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600, lineHeight: 1.2 }}>{user.first_name || 'Khách'} {user.last_name}</span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{user.role}</span>
                </div>
              </div>
              <button onClick={handleLogout} className="btn" style={{ padding: '8px', background: 'var(--color-surface-elevated)', border: '1px solid var(--color-border)', borderRadius: '8px', color: 'var(--color-text-secondary)', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                <LogOut size={16} />
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', gap: '12px' }}>
              <Link to="/login" className="btn btn-outline" style={{ padding: '8px 16px', fontSize: '0.9rem' }}>Đăng nhập</Link>
            </div>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button className="mobile-only" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '8px' }}>
          {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
        </button>
      </div>

      {/* Mobile nav panel */}
      {mobileMenuOpen && (
        <div style={{ position: 'absolute', top: 'var(--header-height)', left: 0, right: 0, background: 'var(--color-surface)', borderBottom: '1px solid var(--color-border)', padding: '16px 20px', display: 'flex', flexDirection: 'column', gap: '16px', zIndex: 90, boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}>
          <Link to="/" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--color-text)', textDecoration: 'none', padding: '8px 0', borderBottom: '1px solid var(--color-border)' }}>Sản phẩm</Link>
          {user && <Link to="/orders" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--color-text)', textDecoration: 'none', padding: '8px 0', borderBottom: '1px solid var(--color-border)' }}>Đơn hàng của tôi</Link>}
          <Link to="/cart" onClick={() => setMobileMenuOpen(false)} style={{ fontSize: '1rem', fontWeight: 500, color: 'var(--color-text)', textDecoration: 'none', padding: '8px 0', borderBottom: '1px solid var(--color-border)', display: 'flex', justifyContent: 'space-between' }}>
            Giỏ hàng <span style={{ background: 'var(--color-primary)', color: 'white', padding: '2px 8px', borderRadius: '12px', fontSize: '0.8rem' }}>{cartCount}</span>
          </Link>
          
          <div style={{ marginTop: '8px' }}>
            {user ? (
               <button onClick={handleLogout} className="btn btn-outline" style={{ width: '100%', justifyContent: 'center', display: 'flex', alignItems: 'center', gap: '8px' }}>
                 <LogOut size={16} /> Đăng xuất
               </button>
            ) : (
               <Link to="/login" onClick={() => setMobileMenuOpen(false)} className="btn btn-primary" style={{ width: '100%', justifyContent: 'center', display: 'flex' }}>
                 Đăng nhập
               </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
