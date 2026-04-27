import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };

function slugify(str) {
  return str.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '').replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
}

export default function AdminCategories() {
  const [cats, setCats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modal, setModal] = useState(null); // null | 'new' | category
  const [form, setForm] = useState({ name: '', slug: '', description: '', is_active: true });
  const [error, setError] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const res = await axios.get(`${API}/products/categories/`, { headers: authHeader() });
      const data = res.data;
      setCats(Array.isArray(data) ? data : (data.results || []));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const openNew = () => {
    setForm({ name: '', slug: '', description: '', is_active: true });
    setError('');
    setModal('new');
  };

  const openEdit = (cat) => {
    setForm({ name: cat.name, slug: cat.slug, description: cat.description || '', is_active: cat.is_active });
    setError('');
    setModal(cat);
  };

  const handleNameChange = (name) => {
    setForm(f => ({ ...f, name, slug: modal === 'new' ? slugify(name) : f.slug }));
  };

  const submit = async (e) => {
    e.preventDefault(); setError('');
    try {
      if (modal === 'new') {
        await axios.post(`${API}/products/categories/`, form, { headers: authHeader() });
      } else {
        await axios.put(`${API}/products/categories/${modal.slug}/`, form, { headers: authHeader() });
      }
      setModal(null);
      load();
    } catch (err) { setError(JSON.stringify(err.response?.data) || 'Lỗi'); }
  };

  const deleteCat = async (slug) => {
    if (!window.confirm('Xóa danh mục này? Các sản phẩm thuộc danh mục này có thể bị ảnh hưởng.')) return;
    try { await axios.delete(`${API}/products/categories/${slug}/`, { headers: authHeader() }); load(); }
    catch { alert('Xóa thất bại'); }
  };

  return (
    <AdminLayout title="Quản lý danh mục">
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 24 }}>
        <button onClick={openNew} style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
          <Plus size={16} /> Thêm danh mục
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 16 }}>
        {loading ? <div style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)', gridColumn: '1 / -1' }}>Đang tải...</div>
          : cats.map(cat => (
          <div key={cat.slug} style={{ background: 'var(--color-surface-elevated)', borderRadius: 14, padding: '20px', border: '1px solid var(--color-border)', opacity: cat.is_active ? 1 : 0.6 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
              <div>
                <div style={{ fontWeight: 700, fontSize: '1rem', marginBottom: 2 }}>{cat.name}</div>
                <div style={{ color: 'var(--color-text-muted)', fontSize: '0.8rem', fontFamily: 'monospace' }}>{cat.slug}</div>
              </div>
              <div style={{ display: 'flex', gap: 6 }}>
                <button onClick={() => openEdit(cat)} style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}><Edit2 size={14} /></button>
                <button onClick={() => deleteCat(cat.slug)} style={{ background: '#ef444422', color: '#ef4444', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}><Trash2 size={14} /></button>
              </div>
            </div>
            {cat.description && <p style={{ fontSize: '0.82rem', color: 'var(--color-text-muted)', margin: '8px 0' }}>{cat.description}</p>}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 12 }}>
              <span style={{ fontSize: '0.8rem', background: '#6366f122', color: '#6366f1', padding: '2px 8px', borderRadius: 5 }}>{cat.product_count || 0} sản phẩm</span>
              <span style={{ fontSize: '0.8rem', color: cat.is_active ? '#16a34a' : '#6b7280', fontWeight: 600 }}>{cat.is_active ? 'Hiển thị' : 'Ẩn'}</span>
            </div>
          </div>
        ))}
      </div>

      {/* Modal */}
      {modal !== null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999 }}>
          <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: 32, minWidth: 400, maxWidth: 500, width: '90%' }}>
            <h3 style={{ marginBottom: 20 }}>{modal === 'new' ? 'Thêm danh mục' : `Sửa: ${modal.name}`}</h3>
            <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Tên danh mục *</label>
                <input value={form.name} onChange={e => handleNameChange(e.target.value)} required
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Slug (URL) *</label>
                <input value={form.slug} onChange={e => setForm(f => ({ ...f, slug: e.target.value }))} required
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box', fontFamily: 'monospace' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Mô tả</label>
                <textarea value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} rows={3}
                  style={{ width: '100%', padding: '10px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', resize: 'vertical', boxSizing: 'border-box' }} />
              </div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.9rem' }}>
                <input type="checkbox" checked={form.is_active} onChange={e => setForm(f => ({ ...f, is_active: e.target.checked }))} />
                Hiển thị danh mục
              </label>
              {error && <div style={{ color: '#ef4444', fontSize: '0.85rem' }}>{error}</div>}
              <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" onClick={() => setModal(null)} style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer' }}>Hủy</button>
                <button type="submit" style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
