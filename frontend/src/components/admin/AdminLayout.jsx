import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import AdminSidebar from './AdminSidebar';

export function AdminRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== 'admin') return <Navigate to="/" replace />;
  return children;
}

export function StaffRoute({ children }) {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;
  if (!['admin', 'staff'].includes(user.role)) return <Navigate to="/" replace />;
  return children;
}

export default function AdminLayout({ children, title }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-bg)' }}>
      <AdminSidebar />
      <div style={{ flex: 1, marginLeft: '260px', padding: '32px', overflowY: 'auto' }}>
        {title && (
          <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '24px', color: 'var(--color-text)' }}>
            {title}
          </h1>
        )}
        {children}
      </div>
    </div>
  );
}
