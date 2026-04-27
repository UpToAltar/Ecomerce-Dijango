import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Search, Plus, Trash2, Edit2, UserCheck, UserX, RefreshCw } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };

const ROLE_LABELS = { admin: 'Admin', staff: 'Nhân viên', customer: 'Khách hàng' };
const ROLE_COLORS = { admin: '#6366f1', staff: '#0ea5e9', customer: '#16a34a' };

export default function AdminUsers() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [roleFilter, setRoleFilter] = useState('');
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ email: '', password: '', first_name: '', last_name: '', phone: '' });
  const [formError, setFormError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const params = roleFilter ? `?role=${roleFilter}` : '';
      const res = await axios.get(`${API}/auth/users/${params}`, { headers: authHeader() });
      let data = Array.isArray(res.data) ? res.data : (res.data.results || []);
      if (search) data = data.filter(u => u.email.includes(search) || u.first_name?.includes(search) || u.last_name?.includes(search));
      setUsers(data);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [roleFilter, search]);

  const toggleStatus = async (user) => {
    try {
      await axios.put(`${API}/auth/users/${user.id}/status/`, { is_active: !user.is_active }, { headers: authHeader() });
      load();
    } catch { alert('Cập nhật thất bại'); }
  };

  const deleteUser = async (id) => {
    if (!window.confirm('Xóa người dùng này?')) return;
    try { await axios.delete(`${API}/auth/users/${id}/`, { headers: authHeader() }); load(); }
    catch { alert('Xóa thất bại'); }
  };

  const submitCreate = async (e) => {
    e.preventDefault(); setFormError('');
    try {
      await axios.post(`${API}/auth/users/create-staff/`, form, { headers: authHeader() });
      setShowModal(false);
      setForm({ email: '', password: '', first_name: '', last_name: '', phone: '' });
      load();
    } catch (err) { setFormError(err.response?.data?.error || JSON.stringify(err.response?.data) || 'Lỗi'); }
  };

  return (
    <AdminLayout title="Quản lý người dùng">
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm email / tên..."
            style={{ width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
        </div>
        <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
          style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
          <option value="">Tất cả vai trò</option>
          {Object.entries(ROLE_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <button onClick={load} style={{ padding: '10px 16px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <RefreshCw size={16} />
        </button>
        <button onClick={() => setShowModal(true)} style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
          <Plus size={16} /> Tạo Staff
        </button>
      </div>

      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'var(--color-surface)' }}>
            <tr>
              {['Họ tên', 'Email', 'Vai trò', 'Điện thoại', 'Trạng thái', 'Ngày tạo', 'Hành động'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, borderBottom: '1px solid var(--color-border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</td></tr>
              : users.length === 0 ? <tr><td colSpan={7} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có người dùng</td></tr>
              : users.map(u => (
              <tr key={u.id} style={{ borderBottom: '1px solid var(--color-border)', opacity: u.is_active ? 1 : 0.5 }}>
                <td style={{ padding: '12px 16px', fontWeight: 600, fontSize: '0.85rem' }}>{u.full_name || `${u.first_name} ${u.last_name}`}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{u.email}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ background: (ROLE_COLORS[u.role] || '#6b7280') + '22', color: ROLE_COLORS[u.role] || '#6b7280', padding: '3px 10px', borderRadius: 6, fontSize: '0.8rem', fontWeight: 600 }}>{ROLE_LABELS[u.role] || u.role}</span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{u.phone || '—'}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ color: u.is_active ? '#16a34a' : '#ef4444', fontWeight: 600, fontSize: '0.85rem' }}>{u.is_active ? 'Hoạt động' : 'Bị khóa'}</span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>{new Date(u.created_at).toLocaleDateString('vi-VN')}</td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => toggleStatus(u)} title={u.is_active ? 'Khóa' : 'Mở khóa'}
                      style={{ background: u.is_active ? '#ef444422' : '#16a34a22', color: u.is_active ? '#ef4444' : '#16a34a', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                      {u.is_active ? <UserX size={14} /> : <UserCheck size={14} />}
                    </button>
                    {u.role !== 'admin' && (
                      <button onClick={() => deleteUser(u.id)} title="Xóa" style={{ background: '#ef444422', color: '#ef4444', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                        <Trash2 size={14} />
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>Tổng: {users.length} người dùng</div>
      </div>

      {/* Create Staff Modal */}
      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: 32, minWidth: 400, width: '90%', maxWidth: 480 }}>
            <h3 style={{ marginBottom: 20 }}>Tạo tài khoản Staff</h3>
            <form onSubmit={submitCreate} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[['email', 'Email *', 'email', 'nhân viên@email.com'], ['password', 'Mật khẩu *', 'password', 'Ít nhất 6 ký tự'], ['first_name', 'Họ'], ['last_name', 'Tên'], ['phone', 'Điện thoại']].map(([field, label, type, placeholder]) => (
                <div key={field}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>{label || field.replace('_', ' ')}</label>
                  <input type={type || 'text'} value={form[field]} onChange={e => setForm(f => ({ ...f, [field]: e.target.value }))} placeholder={placeholder}
                    style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
                </div>
              ))}
              {formError && <div style={{ color: '#ef4444', fontSize: '0.85rem' }}>{formError}</div>}
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" onClick={() => { setShowModal(false); setFormError(''); }} style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer' }}>Hủy</button>
                <button type="submit" style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Tạo</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
