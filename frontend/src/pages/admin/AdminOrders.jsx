import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Eye, Trash2, RefreshCw } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';
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

const authHeader = () => {
  const t = localStorage.getItem('access_token');
  return t ? { Authorization: `Bearer ${t}` } : {};
};

export default function AdminOrders() {
  const navigate = useNavigate();
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [updatingId, setUpdatingId] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      params.set('limit', '100');
      const res = await axios.get(`${API}/orders/admin/?${params}`, { headers: authHeader() });
      setOrders(Array.isArray(res.data) ? res.data : []);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [search, statusFilter]);

  const updateStatus = async (orderId, newStatus) => {
    setUpdatingId(orderId);
    try {
      await axios.put(`${API}/orders/${orderId}/status/`, { status: newStatus }, { headers: authHeader() });
      load();
    } catch { alert('Cập nhật thất bại'); }
    setUpdatingId(null);
  };

  const deleteOrder = async (orderId) => {
    if (!window.confirm('Xóa đơn hàng đã hủy?')) return;
    try {
      await axios.delete(`${API}/orders/${orderId}/delete/`, { headers: authHeader() });
      setOrders(o => o.filter(x => x.id !== orderId));
    } catch (e) { alert(e.response?.data?.error || 'Xóa thất bại'); }
  };

  return (
    <AdminLayout title="Quản lý đơn hàng">
      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input
            value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Tìm mã đơn hàng..."
            style={{ width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.9rem', boxSizing: 'border-box' }}
          />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
          <option value="">Tất cả trạng thái</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={load} style={{ padding: '10px 16px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <RefreshCw size={16} /> Làm mới
        </button>
      </div>

      {/* Table */}
      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'var(--color-surface)' }}>
            <tr>
              {['Mã đơn', 'Tổng tiền', 'Thanh toán', 'Trạng thái', 'Ngày tạo', 'Cập nhật trạng thái', 'Hành động'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, borderBottom: '1px solid var(--color-border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</td></tr>
            ) : orders.length === 0 ? (
              <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có đơn hàng</td></tr>
            ) : orders.map(o => (
              <tr key={o.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 16px', fontWeight: 600, fontFamily: 'monospace', fontSize: '0.85rem' }}>{o.order_number}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', fontWeight: 600 }}>{VND(o.total_amount)}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{o.payment_method?.toUpperCase()}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{
                    background: (STATUS_COLORS[o.status] || '#6b7280') + '22',
                    color: STATUS_COLORS[o.status] || '#6b7280',
                    padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600,
                  }}>{STATUS_LABELS[o.status] || o.status}</span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                  {new Date(o.created_at).toLocaleDateString('vi-VN')}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <select
                    value={o.status}
                    disabled={updatingId === o.id || ['delivered', 'cancelled'].includes(o.status)}
                    onChange={e => updateStatus(o.id, e.target.value)}
                    style={{ padding: '5px 8px', borderRadius: 6, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', fontSize: '0.8rem', cursor: 'pointer' }}
                  >
                    {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => navigate(`/admin/orders/${o.id}`)} title="Xem chi tiết"
                      style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                      <Eye size={14} />
                    </button>
                    {o.status === 'cancelled' && (
                      <button onClick={() => deleteOrder(o.id)} title="Xóa đơn"
                        style={{ background: '#ef444422', color: '#ef4444', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer', display: 'flex', alignItems: 'center' }}>
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>
          Tổng: {orders.length} đơn hàng
        </div>
      </div>
    </AdminLayout>
  );
}
