import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const CartContext = createContext();
export const useCart = () => useContext(CartContext);

const API = 'http://localhost:8000/api';

export const CartProvider = ({ children }) => {
  const { user } = useAuth();
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) {
      fetchCart();
    } else {
      setCartItems([]);
    }
  }, [user]);

  const fetchCart = async () => {
    if (!user) return;
    try {
      setLoading(true);
      const res = await axios.get(`${API}/cart/?user_id=${user.id}`);
      // Normalize cart items from backend format
      const items = (res.data || []).map(item => ({
        id: item.id,
        product_id: item.product_id,
        product_name: item.product_name || item.product_id,
        product_image: item.product_image || '',
        price: parseFloat(item.price || item.product_price || 0),
        quantity: item.quantity,
      }));
      setCartItems(items);
    } catch (err) {
      console.warn('Cart fetch failed:', err.message);
      setCartItems([]);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product, quantity = 1) => {
    if (!user) {
      alert('Vui lòng đăng nhập để thêm sản phẩm vào giỏ');
      return;
    }
    // Optimistic update locally
    setCartItems(prev => {
      const exists = prev.find(i => i.product_id === product.id);
      if (exists) {
        return prev.map(i => i.product_id === product.id
          ? { ...i, quantity: i.quantity + quantity }
          : i
        );
      }
      return [...prev, {
        id: Date.now(),
        product_id: product.id,
        product_name: product.name,
        product_image: product.image_url || '',
        price: parseFloat(product.price),
        quantity,
      }];
    });
    try {
      await axios.post(`${API}/cart/add/`, {
        user_id: user.id,
        product_id: product.id,
        quantity,
      });
    } catch (err) {
      console.warn('Cart API add failed (local state updated):', err.message);
    }
  };

  const removeItem = async (productId) => {
    setCartItems(prev => prev.filter(i => i.product_id !== productId));
    try {
      await axios.delete(`${API}/cart/remove/`, { params: { user_id: user?.id, product_id: productId } });
    } catch (_) {}
  };

  const updateQuantity = async (productId, qty) => {
    if (qty < 1) { removeItem(productId); return; }
    setCartItems(prev => prev.map(i => i.product_id === productId ? { ...i, quantity: qty } : i));
    try {
      await axios.patch(`${API}/cart/update/`, { user_id: user?.id, product_id: productId, quantity: qty });
    } catch (_) {}
  };

  const clearCart = async () => {
    setCartItems([]);
    try {
      if (user) await axios.delete(`${API}/cart/clear/?user_id=${user.id}`);
    } catch (_) {}
  };

  const cartCount = cartItems.reduce((sum, i) => sum + i.quantity, 0);
  const cartTotal = cartItems.reduce((sum, i) => sum + i.price * i.quantity, 0);

  return (
    <CartContext.Provider value={{ cartItems, loading, addToCart, removeItem, updateQuantity, clearCart, cartCount, cartTotal }}>
      {children}
    </CartContext.Provider>
  );
};
