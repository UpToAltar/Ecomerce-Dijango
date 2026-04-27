import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Eye, RefreshCw } from 'lucide-react';
import { StaffLayout } from './StaffDashboard';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };
const VND = (n) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n || 0);
const STATUS_LABELS = { pending: 'Chờ xử lý', confirmed: 'Đã xác nhận', paid: 'Đã thanh toán', shipping: 'Đang giao', delivered: 'Đã giao', cancelled: 'Đã hủy' };
const STATUS_COLORS = { pending: '#eab308', confirmed: '#3b82f6', paid: '#8b5cf6', shipping: '#f59e0b', delivered: '#16a34a', cancelled: '#ef4444' };

export default function StaffOrders() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [updatingId, setUpdatingId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? `?status=${statusFilter}&limit=100` : '?limit=100';
      const res = await axios.get(`${API}/orders/admin/${params}`, { headers: authHeader() });
      setOrders(Array.isArray(res.data) ? res.data : []);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const updateStatus = async (orderId, newStatus) => {
    setUpdatingId(orderId);
    try {
      await axios.put(`${API}/orders/${orderId}/status/`, { status: newStatus }, { headers: authHeader() });
      load();
    } catch { alert('Cập nhật thất bại'); }
    setUpdatingId(null);
  };

  return (
    <StaffLayout title="Quản lý đơn hàng">
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        {['', 'pending', 'confirmed', 'paid', 'shipping', 'delivered'].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--color-border)', cursor: 'pointer', fontWeight: s === statusFilter ? 700 : 400, background: s === statusFilter ? 'var(--color-primary)' : 'var(--color-surface)', color: s === statusFilter ? 'white' : 'var(--color-text)', fontSize: '0.85rem' }}>
            {s ? STATUS_LABELS[s] : 'Tất cả'}
          </button>
        ))}
        <button onClick={load} style={{ padding: '8px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', marginLeft: 'auto' }}>
          <RefreshCw size={16} />
        </button>
      </div>

      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'var(--color-surface)' }}>
            <tr>
              {['Mã đơn', 'Tổng tiền', 'Thanh toán', 'Trạng thái', 'Ngày tạo', 'Cập nhật nhanh', 'Chi tiết'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, borderBottom: '1px solid var(--color-border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</td></tr>
              : orders.length === 0 ? <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có đơn hàng</td></tr>
              : orders.map(o => (
              <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 16px', fontWeight: 600, fontFamily: 'monospace', fontSize: '0.85rem' }}>{o.order_number}</td>
                <td style={{ padding: '12px 16px', fontWeight: 600, fontSize: '0.85rem' }}>{VND(o.total_amount)}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{o.payment_method?.toUpperCase()}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ background: (STATUS_COLORS[o.status]||'#6b7280')+'22', color: STATUS_COLORS[o.status]||'#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600 }}>
                    {STATUS_LABELS[o.status]}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(o.created_at).toLocaleDateString('vi-VN')}</td>
                <td style={{ padding: '12px 16px' }}>
                  {o.status === 'pending' && (
                    <button onClick={() => updateStatus(o.id, 'confirmed')} disabled={updatingId === o.id}
                      style={{ padding: '5px 12px', borderRadius: 6, background: '#3b82f622', color: '#3b82f6', border: 'none', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                      ✓ Xác nhận
                    </button>
                  )}
                  {o.status === 'confirmed' && (
                    <button onClick={() => updateStatus(o.id, 'shipping')} disabled={updatingId === o.id}
                      style={{ padding: '5px 12px', borderRadius: 6, background: '#f59e0b22', color: '#f59e0b', border: 'none', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                      🚚 Giao hàng
                    </button>
                  )}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <button onClick={() => navigate(`/staff/orders/${o.id}`)}
                    style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                    <Eye size={14} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>Tổng: {orders.length} đơn</div>
      </div>
    </StaffLayout>
  );
}
