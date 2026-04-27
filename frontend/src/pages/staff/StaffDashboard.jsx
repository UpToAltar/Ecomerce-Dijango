import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShoppingBag, Truck, Clock, CheckCircle } from 'lucide-react';
import StaffSidebar from '../../components/staff/StaffSidebar';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };
const VND = (n) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n || 0);
const STATUS_LABELS = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', paid: 'Đã thanh toán', shipping: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const STATUS_COLORS = { pending: '#eab308', confirmed: '#3b82f6', paid: '#8b5cf6', shipping: '#f59e0b', delivered: '#16a34a', cancelled: '#ef4444' };

function StaffLayout({ title, children }) {
  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--color-bg)' }}>
      <StaffSidebar />
      <div style={{ flex: 1, marginLeft: '240px', padding: '32px', overflowY: 'auto' }}>
        {title && <h1 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '24px', color: 'var(--color-text)' }}>{title}</h1>}
        {children}
      </div>
    </div>
  );
}

export { StaffLayout };

function StatCard({ icon: Icon, label, value, color }) {
  return (
    <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)', display: 'flex', gap: 16, alignItems: 'flex-start' }}>
      <div style={{ width: 48, height: 48, borderRadius: 12, background: color + '22', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--color-text)' }}>{value}</div>
      </div>
    </div>
  );
}

export default function StaffDashboard() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const res = await axios.get(`${API}/orders/admin/?limit=50`, { headers: authHeader() });
        setOrders(Array.isArray(res.data) ? res.data : []);
      } finally { setLoading(false); }
    };
    load();
  }, []);

  const pending = orders.filter(o => o.status === 'pending').length;
  const shipping = orders.filter(o => o.status === 'shipping').length;
  const confirmed = orders.filter(o => o.status === 'confirmed').length;
  const delivered = orders.filter(o => o.status === 'delivered').length;

  const urgent = orders.filter(o => ['pending', 'confirmed'].includes(o.status)).slice(0, 10);

  return (
    <StaffLayout title="Bảng điều khiển">
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <StatCard icon={Clock} label="Chờ xử lý" value={pending} color="#eab308" />
        <StatCard icon={CheckCircle} label="Đã xác nhận" value={confirmed} color="#3b82f6" />
        <StatCard icon={Truck} label="Đang giao" value={shipping} color="#f59e0b" />
        <StatCard icon={ShoppingBag} label="Đã hoàn thành" value={delivered} color="#16a34a" />
      </div>

      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: '1rem' }}>Đơn cần xử lý</h3>
          <button onClick={() => navigate('/staff/orders')} style={{ background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontSize: '0.85rem' }}>Xem tất cả →</button>
        </div>
        {loading ? <div style={{ textAlign: 'center', padding: 40, color: 'var(--color-text-muted)' }}>Đang tải...</div> : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead><tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              {['Mã đơn', 'Tổng tiền', 'Trạng thái', 'Ngày tạo', 'Hành động'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>{h}</th>
              ))}
            </tr></thead>
            <tbody>
              {urgent.map(o => (
                <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '10px 12px', fontWeight: 600, fontFamily: 'monospace', fontSize: '0.85rem' }}>{o.order_number}</td>
                  <td style={{ padding: '10px 12px', fontWeight: 600, fontSize: '0.85rem' }}>{VND(o.total_amount)}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <span style={{ background: (STATUS_COLORS[o.status] || '#6b7280') + '22', color: STATUS_COLORS[o.status] || '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600 }}>
                      {STATUS_LABELS[o.status]}
                    </span>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(o.created_at).toLocaleDateString('vi-VN')}</td>
                  <td style={{ padding: '10px 12px' }}>
                    <button onClick={() => navigate(`/staff/orders/${o.id}`)} style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 12px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>Xử lý</button>
                  </td>
                </tr>
              ))}
              {urgent.length === 0 && <tr><td colSpan={5} style={{ padding: 30, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có đơn cần xử lý</td></tr>}
            </tbody>
          </table>
        )}
      </div>
    </StaffLayout>
  );
}
