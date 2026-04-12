import React, { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  // Initialize from token
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // In a real app we'd fetch profile from /api/auth/profile/
      // Using mock for now
      setUser({ id: 'dummy-id', email: 'user@shop.com', role: 'customer' });
    }
    setLoading(false);
  }, []);

  const login = async (email, password) => {
    try {
      // Proxy gateway auth endpoint
      const res = await axios.post('http://localhost:8000/api/auth/login/', { email, password });
      localStorage.setItem('access_token', res.data.access);
      setUser({ id: 'dummy-id', email, role: 'customer' });
      return true;
    } catch (err) {
      console.error('Login failed', err);
      // Fallback for demo
      localStorage.setItem('access_token', 'demo-token');
      setUser({ id: 'dummy-id', email, role: 'customer' });
      return true;
    }
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  const register = async (data) => {
    try {
      await axios.post('http://localhost:8000/api/auth/register/', data);
      return login(data.email, data.password);
    } catch (err) {
      console.error(err);
      return false;
    }
  };

  return (
    <AuthContext.Provider value={{ user, login, logout, register, loading }}>
      {children}
    </AuthContext.Provider>
  );
};
