import React from 'react';
import { BrowserRouter as Router, Routes, Route, useLocation } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { CartProvider } from './context/CartContext';
import Header from './components/Header';
import AIChatWidget from './components/AIChatWidget';
import Home from './pages/Home';
import ProductDetail from './pages/ProductDetail';
import Login from './pages/Login';
import Register from './pages/Register';
import Cart from './pages/Cart';
import Checkout from './pages/Checkout';
import PaymentResult from './pages/PaymentResult';
import Orders from './pages/Orders';
import OrderDetail from './pages/OrderDetail';
import AIChat from './pages/AIChat';

function AppContent() {
  const location = useLocation();
  const hiddenWidget = location.pathname === '/ai-chat';

  return (
    <div className="app">
      <Header />
      {location.pathname === '/ai-chat' ? (
        <div style={{ paddingTop: 'var(--header-height)', flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', height: '100vh' }}>
          <AIChat />
        </div>
      ) : (
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/products/:slug" element={<ProductDetail />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/cart" element={<Cart />} />
            <Route path="/checkout" element={<Checkout />} />
            <Route path="/payment-result" element={<PaymentResult />} />
            <Route path="/orders" element={<Orders />} />
            <Route path="/orders/:id" element={<OrderDetail />} />
            <Route path="/ai-chat" element={<AIChat />} />
          </Routes>
        </main>
      )}
      {!hiddenWidget && <AIChatWidget />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <CartProvider>
        <Router>
          <AppContent />
        </Router>
      </CartProvider>
    </AuthProvider>
  );
}

export default App;
