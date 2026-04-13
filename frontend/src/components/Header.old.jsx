import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ShoppingCart, Search, User, LogOut } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useCart } from '../context/CartContext';

export default function Header() {
  const { user, logout } = useAuth();
  const { cartItems } = useCart();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <header className="header" id="main-header">
      <div className="container header-content">
        <Link to="/" className="logo" id="logo">Lumina.</Link>
        
        <nav className="nav-links">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/" className="nav-link">Shop</Link>
          <Link to="/" className="nav-link">Categories</Link>
        </nav>

        <div className="header-actions">
          <button className="icon-btn" aria-label="Search">
            <Search size={20} />
          </button>
          
          {user ? (
            <>
              <button className="icon-btn" title="Profile" onClick={() => navigate('/orders')}>
                <User size={20} />
              </button>
              <button className="icon-btn" title="Logout" onClick={handleLogout}>
                <LogOut size={20} />
              </button>
            </>
          ) : (
            <Link to="/login" className="btn btn-primary" style={{ padding: '8px 16px', fontSize: '0.85rem' }}>
              Sign In
            </Link>
          )}

          <Link to="/cart" className="icon-btn" aria-label="Shopping Cart">
            <ShoppingCart size={20} />
            {cartItems?.length > 0 && (
              <span className="badge">{cartItems.length}</span>
            )}
          </Link>
        </div>
      </div>
    </header>
  );
}
