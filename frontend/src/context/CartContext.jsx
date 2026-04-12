import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const CartContext = createContext();

export const useCart = () => useContext(CartContext);

export const CartProvider = ({ children }) => {
  const { user } = useAuth();
  const [cartItems, setCartItems] = useState([]);
  const [loading, setLoading] = useState(false);

  // Sync cart with backend when user changes
  useEffect(() => {
    if (user) {
      fetchCart();
    } else {
      setCartItems([]);
    }
  }, [user]);

  const fetchCart = async () => {
    try {
      setLoading(true);
      const res = await axios.get(`http://localhost:8000/api/cart/?user_id=${user.id}`);
      setCartItems(res.data);
    } catch (err) {
      console.warn('Failed to fetch cart. Using dummy empty cart.');
      setCartItems([]);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = async (product, quantity = 1) => {
    if (!user) {
      alert("Please login to add to cart");
      return;
    }
    
    try {
      await axios.post('http://localhost:8000/api/cart/add/', {
        user_id: user.id,
        product_id: product.id,
        quantity
      });
      fetchCart();
    } catch (err) {
      console.error("Cart add error", err);
      // Fallback
      setCartItems(prev => [...prev, { id: Date.now(), product_id: product.id, quantity }]);
    }
  };

  const clearCart = async () => {
    if (user) {
      try {
        await axios.delete(`http://localhost:8000/api/cart/clear/?user_id=${user.id}`);
        setCartItems([]);
      } catch(err) {
        setCartItems([]);
      }
    }
  };

  return (
    <CartContext.Provider value={{ cartItems, loading, addToCart, clearCart }}>
      {children}
    </CartContext.Provider>
  );
};
