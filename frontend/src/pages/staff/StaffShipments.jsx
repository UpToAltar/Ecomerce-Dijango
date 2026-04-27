import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { RefreshCw } from 'lucide-react';
import { StaffLayout } from './StaffDashboard';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };
const SHIP_COLORS = { pending: '#eab308', picked_up: '#3b82f6', in_transit: '#8b5cf6', out_for_delivery: '#f59e0b', delivered: '#16a34a', failed: '#ef4444', returned: '#6b7280' };
const SHIP_LABELS = { pending: 'Chờ xử lý', picked_up: 'Đã lấy hàng', in_transit: 'Đang vận chuyển', out_for_delivery: 'Đang giao', delivered: 'Đã giao', failed: 'Thất bại', returned: 'Đã hoàn trả' };

export default function StaffShipments() {
  const [shipments, setShipments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [modal, setModal] = useState(null);
  const [updateStatus, setUpdateStatus] = useState('');
  const [location, setLocation] = useState('');
  const [note, setNote] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const res = await axios.get(`${API}/shipping/admin/${params}`, { headers: authHeader() });
      setShipments(Array.isArray(res.data) ? res.data : []);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [statusFilter]);

  const openModal = (s) => { setModal(s); setUpdateStatus(s.status); setLocation(''); setNote(''); };

  const submitUpdate = async (e) => {
    e.preventDefault();
    try {
      await axios.put(`${API}/shipping/${modal.id}/status/`, { status: updateStatus, location, note }, { headers: authHeader() });
      setModal(null);
      load();
    } catch { alert('Cập nhật thất bại'); }
  };

  return (
    <StaffLayout title="Quản lý vận chuyển">
      <div style={{ display: 'flex', gap: 8, marginBottom: 24, flexWrap: 'wrap' }}>
        {['', ...Object.keys(SHIP_LABELS)].map(s => (
          <button key={s} onClick={() => setStatusFilter(s)}
            style={{ padding: '7px 14px', borderRadius: 8, border: '1px solid var(--color-border)', cursor: 'pointer', fontWeight: s === statusFilter ? 700 : 400, background: s === statusFilter ? 'var(--color-primary)' : 'var(--color-surface)', color: s === statusFilter ? 'white' : 'var(--color-text)', fontSize: '0.8rem' }}>
            {s ? SHIP_LABELS[s] : 'Tất cả'}
          </button>
        ))}
        <button onClick={load} style={{ padding: '7px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', marginLeft: 'auto' }}>
          <RefreshCw size={16} />
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
                  <span style={{ background: (SHIP_COLORS[s.status]||'#6b7280')+'22', color: SHIP_COLORS[s.status]||'#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600 }}>
                    {SHIP_LABELS[s.status]||s.status}
                  </span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(s.created_at).toLocaleDateString('vi-VN')}</td>
                <td style={{ padding: '12px 16px' }}>
                  <button onClick={() => openModal(s)} style={{ background: '#16a34a22', color: '#16a34a', border: 'none', borderRadius: 6, padding: '5px 12px', cursor: 'pointer', fontSize: '0.8rem', fontWeight: 600 }}>
                    Cập nhật
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>Tổng: {shipments.length} vận đơn</div>
      </div>

      {modal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: 32, minWidth: 400, maxWidth: 500, width: '90%' }}>
            <h3 style={{ marginBottom: 20 }}>Cập nhật: {modal.tracking_number}</h3>
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
                <button type="button" onClick={() => setModal(null)} style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer' }}>Hủy</button>
                <button type="submit" style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </StaffLayout>
  );
}
