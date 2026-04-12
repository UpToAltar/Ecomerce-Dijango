import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Header from './components/Header';
import Home from './pages/Home';
import Login from './pages/Login';
import Register from './pages/Register';
import Cart from './pages/Cart';
import './index.css';

export default function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Router>
          <div className="app-wrapper">
            <Header />
            <div style={{ paddingTop: '80px' }}>
              <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />
                <Route path="/cart" element={<Cart />} />
              </Routes>
            </div>
          </div>
        </Router>
      </CartProvider>
    </AuthProvider>
  );
}
