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
import AINewRecommend from './pages/AINewRecommend';
import TrackShipment from './pages/TrackShipment';

// Admin pages
import AdminDashboard from './pages/admin/AdminDashboard';
import AdminOrders from './pages/admin/AdminOrders';
import AdminOrderDetail from './pages/admin/AdminOrderDetail';
import AdminShipments from './pages/admin/AdminShipments';
import AdminUsers from './pages/admin/AdminUsers';
import AdminProducts from './pages/admin/AdminProducts';
import AdminCategories from './pages/admin/AdminCategories';
import { AdminRoute, StaffRoute } from './components/admin/AdminLayout';

// Staff pages
import StaffDashboard from './pages/staff/StaffDashboard';
import StaffOrders from './pages/staff/StaffOrders';
import StaffShipments from './pages/staff/StaffShipments';

const DASHBOARD_ROUTES = ['/admin', '/staff'];

function AppContent() {
  const location = useLocation();
  const hiddenWidget = location.pathname === '/ai-chat';
  const isDashboard = DASHBOARD_ROUTES.some(p => location.pathname.startsWith(p));

  if (isDashboard) {
    return (
      <Routes>
        {/* Admin routes */}
        <Route path="/admin" element={<AdminRoute><AdminDashboard /></AdminRoute>} />
        <Route path="/admin/orders" element={<AdminRoute><AdminOrders /></AdminRoute>} />
        <Route path="/admin/orders/:id" element={<AdminRoute><AdminOrderDetail /></AdminRoute>} />
        <Route path="/admin/shipments" element={<AdminRoute><AdminShipments /></AdminRoute>} />
        <Route path="/admin/users" element={<AdminRoute><AdminUsers /></AdminRoute>} />
        <Route path="/admin/products" element={<AdminRoute><AdminProducts /></AdminRoute>} />
        <Route path="/admin/categories" element={<AdminRoute><AdminCategories /></AdminRoute>} />
        {/* Staff routes */}
        <Route path="/staff" element={<StaffRoute><StaffDashboard /></StaffRoute>} />
        <Route path="/staff/orders" element={<StaffRoute><StaffOrders /></StaffRoute>} />
        <Route path="/staff/orders/:id" element={<StaffRoute><AdminOrderDetail /></StaffRoute>} />
        <Route path="/staff/shipments" element={<StaffRoute><StaffShipments /></StaffRoute>} />
      </Routes>
    );
  }

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
            <Route path="/tracking" element={<TrackShipment />} />
            <Route path="/ai-chat" element={<AIChat />} />
            <Route path="/ai-recommend" element={<AINewRecommend />} />
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
