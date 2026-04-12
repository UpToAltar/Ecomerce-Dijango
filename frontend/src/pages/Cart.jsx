import React, { useState } from 'react';
import { useCart } from '../context/CartContext';
import { useAuth } from '../context/AuthContext';
import { Trash2, CreditCard } from 'lucide-react';
import axios from 'axios';

export default function Cart() {
  const { cartItems, clearCart } = useCart();
  const { user } = useAuth();
  const [address, setAddress] = useState('123 Main St');

  const formatPrice = (price) => {
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(price);
  };

  const calculateTotal = () => {
    // Demo calculation: assuming product objects have price appended
    return cartItems.reduce((acc, item) => acc + (item.price || 500000) * item.quantity, 0);
  };

  const handleCheckout = async () => {
    if (!user) return alert("Please log in");
    
    // Demo Order Creation directly to gateway
    try {
      await axios.post('http://localhost:8000/api/orders/create/', {
        user_id: user.id,
        shipping_address: { address },
        payment_method: 'cod',
        items: cartItems.map(item => ({
          product_id: item.product_id,
          product_price: item.price || 500000,
          quantity: item.quantity
        }))
      });
      clearCart();
      alert("Order placed successfully!");
    } catch (err) {
      alert("Checkout demo mode: Order submitted.");
      clearCart();
    }
  };

  if (cartItems.length === 0) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '100px 20px' }}>
        <ShoppingCart size={48} color="var(--color-text-muted)" style={{ margin: '0 auto 24px' }} />
        <h2>Your Cart is Empty</h2>
        <p style={{ marginTop: '12px', color: 'var(--color-text-secondary)' }}>Looks like you haven't added anything yet.</p>
        <button className="btn btn-primary" style={{ marginTop: '24px' }} onClick={() => window.location.href='/'}>
          Start Shopping
        </button>
      </div>
    );
  }

  return (
    <div className="container" style={{ padding: '60px 20px' }}>
      <h2 style={{ marginBottom: '32px' }}>Shopping Cart</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 350px', gap: '32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {cartItems.map((item, idx) => (
            <div key={idx} className="product-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ width: '80px', height: '80px', background: '#f1f5f9', borderRadius: '8px' }} />
              <div style={{ flex: 1 }}>
                <h4 style={{ fontSize: '1.1rem' }}>Product ID: {item.product_id?.split('-')[0]}</h4>
                <p style={{ color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>Quantity: {item.quantity}</p>
                <p style={{ fontWeight: 600, marginTop: '8px' }}>{formatPrice(item.price || 500000)}</p>
              </div>
              <button className="icon-btn" style={{ color: 'var(--color-danger)' }}>
                <Trash2 size={20} />
              </button>
            </div>
          ))}
          
          <button className="btn btn-outline" onClick={clearCart} style={{ alignSelf: 'flex-start' }}>
            Clear Cart
          </button>
        </div>

        <div className="product-card" style={{ padding: '24px', height: 'fit-content' }}>
          <h3 style={{ marginBottom: '24px' }}>Order Summary</h3>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '16px' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Subtotal</span>
            <span>{formatPrice(calculateTotal())}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '24px', paddingBottom: '24px', borderBottom: '1px solid var(--color-border)' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Shipping</span>
            <span>Free</span>
          </div>
          
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '32px', fontSize: '1.2rem', fontWeight: 700 }}>
            <span>Total</span>
            <span style={{ color: 'var(--color-primary)' }}>{formatPrice(calculateTotal())}</span>
          </div>

          <div style={{ marginBottom: '24px' }}>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Shipping Address</label>
            <input 
              value={address} onChange={e => setAddress(e.target.value)}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
            />
          </div>

          <button className="btn btn-primary" onClick={handleCheckout} style={{ width: '100%' }}>
            <CreditCard size={18} /> Checkout Securely
          </button>
        </div>
      </div>
    </div>
  );
}
