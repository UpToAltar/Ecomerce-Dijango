import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, ShoppingBag, Truck, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

const links = [
  { to: '/staff', label: 'Tổng quan', icon: LayoutDashboard, end: true },
  { to: '/staff/orders', label: 'Đơn hàng', icon: ShoppingBag },
  { to: '/staff/shipments', label: 'Vận chuyển', icon: Truck },
];

export default function StaffSidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const handleLogout = () => { logout(); navigate('/login'); };

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, height: '100vh', width: '240px',
      background: 'linear-gradient(180deg, #0f172a 0%, #164e63 100%)',
      display: 'flex', flexDirection: 'column', zIndex: 100,
      boxShadow: '4px 0 20px rgba(0,0,0,0.3)',
    }}>
      <div style={{ padding: '24px 20px', borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: 36, height: 36, borderRadius: 10,
            background: 'linear-gradient(135deg,#0ea5e9,#06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
          }}>
            <span style={{ color: 'white', fontWeight: 800, fontSize: '1rem' }}>S</span>
          </div>
          <div>
            <div style={{ color: 'white', fontWeight: 700, fontSize: '0.95rem' }}>Staff Portal</div>
            <div style={{ color: '#94a3b8', fontSize: '0.75rem' }}>{user?.email}</div>
          </div>
        </div>
      </div>
      <nav style={{ flex: 1, padding: '16px 12px' }}>
        {links.map(({ to, label, icon: Icon, end }) => (
          <NavLink key={to} to={to} end={end}
            style={({ isActive }) => ({
              display: 'flex', alignItems: 'center', gap: '12px',
              padding: '11px 14px', borderRadius: '10px',
              marginBottom: '4px', textDecoration: 'none',
              color: isActive ? 'white' : '#94a3b8',
              background: isActive ? 'rgba(14,165,233,0.25)' : 'transparent',
              fontWeight: isActive ? 600 : 400, fontSize: '0.9rem',
            })}
          >
            <Icon size={18} /><span>{label}</span>
          </NavLink>
        ))}
      </nav>
      <div style={{ padding: '16px 12px', borderTop: '1px solid rgba(255,255,255,0.08)' }}>
        <button onClick={handleLogout} style={{
          width: '100%', display: 'flex', alignItems: 'center', gap: '12px',
          padding: '11px 14px', borderRadius: '10px', border: 'none',
          background: 'transparent', color: '#f87171', cursor: 'pointer', fontSize: '0.9rem',
        }}>
          <LogOut size={18} /> Đăng xuất
        </button>
      </div>
    </div>
  );
}
