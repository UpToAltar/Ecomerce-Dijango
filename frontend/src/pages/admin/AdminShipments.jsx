import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, RefreshCw, Eye } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };

const SHIP_COLORS = { pending: '#eab308', picked_up: '#3b82f6', in_transit: '#8b5cf6', out_for_delivery: '#f59e0b', delivered: '#16a34a', failed: '#ef4444', returned: '#6b7280' };
const SHIP_LABELS = { pending: 'Chờ xử lý', picked_up: 'Đã lấy hàng', in_transit: 'Đang vận chuyển', out_for_delivery: 'Đang giao', delivered: 'Đã giao', failed: 'Thất bại', returned: 'Đã hoàn trả' };

export default function AdminShipments() {
  const navigate = useNavigate();
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [modal, setModal] = useState(null); // { shipment }
  const [updateStatus, setUpdateStatus] = useState('');
  const [location, setLocation] = useState('');
  const [note, setNote] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      if (statusFilter) params.set('status', statusFilter);
      const res = await axios.get(`${API}/shipping/admin/?${params}`, { headers: authHeader() });
      setShipments(Array.isArray(res.data) ? res.data : []);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [search, statusFilter]);

  const openModal = (s) => { setModal(s); setUpdateStatus(s.status); setLocation(''); setNote(''); };
  const closeModal = () => setModal(null);

  const submitUpdate = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/shipping/${modal.id}/status/`, { status: updateStatus, location, note }, { headers: authHeader() });
      closeModal();
      load();
    } catch { alert('Cập nhật thất bại'); }
  };

  return (
    <AdminLayout title="Quản lý vận chuyển">
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm mã vận đơn / đơn hàng..."
            style={{ width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
          <option value="">Tất cả trạng thái</option>
          {Object.entries(SHIP_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={load} style={{ padding: '10px 16px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <RefreshCw size={16} /> Làm mới
        </button>
      </div>

      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'var(--color-surface)' }}>
            <tr>
              {['Mã vận đơn', 'Mã đơn hàng', 'Đơn vị', 'Trạng thái', 'Ngày tạo', 'Hành động'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, borderBottom: '1px solid var(--color-border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</td></tr>
              : shipments.length === 0 ? <tr><td colSpan={6} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có vận đơn</td></tr>
              : shipments.map(s => (
              <tr key={s.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontWeight: 600, fontSize: '0.85rem' }}>{s.tracking_number}</td>
                <td style={{ padding: '12px 16px', fontFamily: 'monospace', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{s.order_number}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem' }}>{s.carrier}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ background: (SHIP_COLORS[s.status] || '#6b7280') + '22', color: SHIP_COLORS[s.status] || '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600 }}>
                    {SHIP_LABELS[s.status] || s.status}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(s.created_at).toLocaleDateString('vi-VN')}</td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    <button onClick={() => navigate(`/admin/orders/${s.order_id}`)} title="Xem đơn hàng"
                      style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                      <Eye size={14} />
                    </button>
                    <button onClick={() => openModal(s)} title="Cập nhật vận đơn"
                      style={{ background: '#16a34a22', color: '#16a34a', border: 'none', borderRadius: 6, padding: '5px 10px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                      Cập nhật
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>Tổng: {shipments.length} vận đơn</div>
      </div>

      {/* Modal */}
      {modal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: 32, minWidth: 400, maxWidth: 520, width: '90%' }}>
            <h3 style={{ marginBottom: 20 }}>Cập nhật vận đơn {modal.tracking_number}</h3>
            <form onSubmit={submitUpdate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Trạng thái</label>
                <select value={updateStatus} onChange={e => setUpdateStatus(e.target.value)}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
                  {Object.entries(SHIP_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                </select>
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Địa điểm</label>
                <input value={location} onChange={e => setLocation(e.target.value)} placeholder="VD: Kho Hà Nội"
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Ghi chú</label>
                <textarea value={note} onChange={e => setNote(e.target.value)} rows={3}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', resize: 'vertical', boxSizing: 'border-box' }} />
              </div>
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
                <button type="button" onClick={closeModal} style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer' }}>Hủy</button>
                <button type="submit" style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
