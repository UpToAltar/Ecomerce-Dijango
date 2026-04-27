import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ShoppingBag, Users, Truck, DollarSign, Clock, CheckCircle, XCircle, Package } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';
import { useAuth } from '../../context/AuthContext';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const VND = (n) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n || 0);

const STATUS_COLORS = {
  pending: '#eab308', confirmed: '#3b82f6', paid: '#8b5cf6',
  shipping: '#f59e0b', delivered: '#16a34a', cancelled: '#ef4444',
};
const STATUS_LABELS = {
  pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', paid: 'Đã thanh toán',
  shipping: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy',
};

function StatCard({ icon: Icon, label, value, color, sub }) {
  return (
    <div style={{
      background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px',
      border: '1px solid var(--color-border)', display: 'flex', gap: 16, alignItems: 'flex-start',
    }}>
      <div style={{
        width: 48, height: 48, borderRadius: 12, background: color + '22',
        display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0,
      }}>
        <Icon size={22} color={color} />
      </div>
      <div>
        <div style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>{label}</div>
        <div style={{ fontSize: '1.7rem', fontWeight: 800, color: 'var(--color-text)', lineHeight: 1.2 }}>{value}</div>
        {sub && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', marginTop: 4 }}>{sub}</div>}
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [userStats, setUserStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const authHeader = () => {
    const token = localStorage.getItem('access_token');
    return token ? { Authorization: `Bearer ${token}` } : {};
  };

  useEffect(() => {
    const load = async () => {
      try {
        const [statsRes, userRes, ordersRes] = await Promise.all([
          axios.get(`${API}/orders/stats/`, { headers: authHeader() }).catch(() => ({ data: {} })),
          axios.get(`${API}/auth/users/stats/`, { headers: authHeader() }).catch(() => ({ data: {} })),
          axios.get(`${API}/orders/admin/?limit=5`, { headers: authHeader() }).catch(() => ({ data: [] })),
        ]);
        setStats(statsRes.data);
        setUserStats(userRes.data);
        setRecentOrders(Array.isArray(ordersRes.data) ? ordersRes.data : []);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  if (loading) return (
    <AdminLayout title="Tổng quan">
      <div style={{ textAlign: 'center', padding: '80px', color: 'var(--color-text-muted)' }}>Đang tải...</div>
    </AdminLayout>
  );

  const byStatus = stats?.by_status || {};
  const totalRevenue = stats?.total_revenue || 0;
  const dailyRevenue = stats?.daily_revenue || [];
  const maxRevenue = Math.max(...dailyRevenue.map(d => Number(d.revenue || 0)), 1);

  return (
    <AdminLayout title="Tổng quan hệ thống">
      {/* Stat Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 32 }}>
        <StatCard icon={ShoppingBag} label="Tổng đơn hàng" value={stats?.total || 0} color="#6366f1" />
        <StatCard icon={DollarSign} label="Doanh thu" value={VND(totalRevenue)} color="#16a34a" />
        <StatCard icon={Clock} label="Chờ xử lý" value={byStatus.pending || 0} color="#eab308" />
        <StatCard icon={Users} label="Người dùng" value={userStats?.total || 0} color="#3b82f6"
          sub={`${userStats?.by_role?.staff || 0} staff`} />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 32 }}>
        {/* Status breakdown */}
        <div style={{
          background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px',
          border: '1px solid var(--color-border)'
        }}>
          <h3 style={{ marginBottom: 16, fontSize: '1rem' }}>Đơn hàng theo trạng thái</h3>
          {Object.entries(STATUS_LABELS).map(([k, label]) => {
            const count = byStatus[k] || 0;
            const pct = stats?.total > 0 ? (count / stats.total) * 100 : 0;
            return (
              <div key={k} style={{ marginBottom: 12 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <span style={{ fontSize: '0.85rem', color: 'var(--color-text-secondary)' }}>{label}</span>
                  <span style={{ fontSize: '0.85rem', fontWeight: 600 }}>{count}</span>
                </div>
                <div style={{ height: 6, background: 'var(--color-border)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ height: '100%', width: `${pct}%`, background: STATUS_COLORS[k] || '#6b7280', borderRadius: 3, transition: 'width 0.5s' }} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Daily revenue bar chart */}
        <div style={{
          background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px',
          border: '1px solid var(--color-border)'
        }}>
          <h3 style={{ marginBottom: 16, fontSize: '1rem' }}>Doanh thu 7 ngày gần nhất</h3>
          {dailyRevenue.length === 0 ? (
            <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: '30px' }}>Chưa có dữ liệu</div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 140 }}>
              {dailyRevenue.map((d, i) => {
                const pct = (Number(d.revenue || 0) / maxRevenue) * 100;
                return (
                  <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
                    <div style={{ fontSize: '0.7rem', color: 'var(--color-text-muted)' }}>{d.count}</div>
                    <div style={{
                      width: '100%', height: `${Math.max(pct, 4)}%`,
                      background: 'linear-gradient(180deg,#6366f1,#8b5cf6)',
                      borderRadius: '4px 4px 0 0', minHeight: 4,
                    }} title={VND(d.revenue)} />
                    <div style={{ fontSize: '0.65rem', color: 'var(--color-text-muted)', textAlign: 'center' }}>
                      {new Date(d.date).toLocaleDateString('vi-VN', { day: '2-digit', month: '2-digit' })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Orders */}
      <div style={{
        background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px',
        border: '1px solid var(--color-border)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ fontSize: '1rem', margin: 0 }}>Đơn hàng gần nhất</h3>
          <button onClick={() => navigate('/admin/orders')} style={{
            background: 'none', border: 'none', color: 'var(--color-primary)', cursor: 'pointer', fontSize: '0.85rem'
          }}>Xem tất cả →</button>
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
              {['Mã đơn', 'Khách hàng', 'Tổng tiền', 'Trạng thái', 'Ngày tạo'].map(h => (
                <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {recentOrders.map(o => (
              <tr key={o.id} onClick={() => navigate(`/admin/orders/${o.id}`)} style={{ borderBottom: '1px solid var(--color-border)', cursor: 'pointer' }}
                onMouseEnter={e => e.currentTarget.style.background = 'var(--color-surface)'}
                onMouseLeave={e => e.currentTarget.style.background = 'transparent'}>
                <td style={{ padding: '10px 12px', fontWeight: 600, fontSize: '0.85rem', fontFamily: 'monospace' }}>{o.order_number}</td>
                <td style={{ padding: '10px 12px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{String(o.user_id).slice(0, 8)}...</td>
                <td style={{ padding: '10px 12px', fontSize: '0.85rem', fontWeight: 600 }}>{VND(o.total_amount)}</td>
                <td style={{ padding: '10px 12px' }}>
                  <span style={{
                    background: (STATUS_COLORS[o.status] || '#6b7280') + '22',
                    color: STATUS_COLORS[o.status] || '#6b7280',
                    padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600
                  }}>{STATUS_LABELS[o.status] || o.status}</span>
                </td>
                <td style={{ padding: '10px 12px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  {new Date(o.created_at).toLocaleDateString('vi-VN')}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AdminLayout>
  );
}
