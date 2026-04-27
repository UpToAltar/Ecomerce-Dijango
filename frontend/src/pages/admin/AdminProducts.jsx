import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Edit2, Trash2, Search, EyeOff, Eye, RefreshCw } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';
const authHeader = () => { const t = localStorage.getItem('access_token'); return t ? { Authorization: `Bearer ${t}` } : {}; };
const VND = (n) => new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(n || 0);

export default function AdminProducts() {
  const navigate = useNavigate();
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [editModal, setEditModal] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [categories, setCategories] = useState([]);

  const load = async () => {
    setLoading(true);
    try {
      const params = search ? `?search=${encodeURIComponent(search)}&is_active=` : '?is_active=';
      const [prodRes, catRes] = await Promise.all([
        axios.get(`${API}/products/${params}`, { headers: authHeader() }),
        axios.get(`${API}/products/categories/`, { headers: authHeader() }),
      ]);
      const data = prodRes.data;
      setProducts(Array.isArray(data) ? data : (data.results || []));
      setCategories(Array.isArray(catRes.data) ? catRes.data : (catRes.data.results || []));
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [search]);

  const openEdit = (p) => {
    setEditForm({
      name: p.name, price: p.price, compare_price: p.compare_price || '',
      stock_quantity: p.stock_quantity, description: p.description,
      category_slug: p.category?.slug || '', is_active: p.is_active, image_url: p.image_url || '',
    });
    setEditModal(p);
  };

  const saveEdit = async (e) => {
    e.preventDefault();
    try {
      await axios.patch(`${API}/products/${editModal.slug}/`, editForm, { headers: authHeader() });
      setEditModal(null);
      load();
    } catch (err) { alert('Cập nhật thất bại: ' + JSON.stringify(err.response?.data)); }
  };

  const deleteProduct = async (slug) => {
    if (!window.confirm('Xóa sản phẩm này?')) return;
    try {
      await axios.delete(`${API}/products/${slug}/`, { headers: authHeader() });
      load();
    } catch { alert('Xóa thất bại'); }
  };

  const toggleActive = async (p) => {
    try {
      await axios.patch(`${API}/products/${p.slug}/`, { is_active: !p.is_active }, { headers: authHeader() });
      load();
    } catch { alert('Cập nhật thất bại'); }
  };

  return (
    <AdminLayout title="Quản lý sản phẩm">
      <div style={{ display: 'flex', gap: 12, marginBottom: 24 }}>
        <div style={{ position: 'relative', flex: 1 }}>
          <Search size={16} style={{ position: 'absolute', left: 12, top: '50%', transform: 'translateY(-50%)', color: 'var(--color-text-muted)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Tìm sản phẩm..."
            style={{ width: '100%', padding: '10px 12px 10px 36px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
        </div>
        <button onClick={load} style={{ padding: '10px 16px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6 }}>
          <RefreshCw size={16} />
        </button>
        <button onClick={() => navigate('/admin/products/new')} style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 8, fontWeight: 600 }}>
          <Plus size={16} /> Thêm sản phẩm
        </button>
      </div>

      <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, border: '1px solid var(--color-border)', overflow: 'hidden' }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ background: 'var(--color-surface)' }}>
            <tr>
              {['', 'Tên sản phẩm', 'Danh mục', 'Giá', 'Tồn kho', 'Đã bán', 'Hiển thị', 'Hành động'].map(h => (
                <th key={h} style={{ padding: '12px 16px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600, borderBottom: '1px solid var(--color-border)' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? <tr><td colSpan={8} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</td></tr>
              : products.length === 0 ? <tr><td colSpan={8} style={{ padding: 40, textAlign: 'center', color: 'var(--color-text-muted)' }}>Không có sản phẩm</td></tr>
            : products.map(p => (
              <tr key={p.slug} style={{ borderBottom: '1px solid var(--color-border)', opacity: p.is_active ? 1 : 0.5 }}>
                <td style={{ padding: '8px 16px' }}>
                  {p.image_url && <img src={p.image_url} alt="" style={{ width: 44, height: 44, objectFit: 'cover', borderRadius: 8 }} />}
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{p.name}</div>
                  <div style={{ color: 'var(--color-text-muted)', fontSize: '0.75rem' }}>{p.sku}</div>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{p.category?.name}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', fontWeight: 600 }}>{VND(p.price)}</td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem' }}>
                  <span style={{ color: p.stock_quantity === 0 ? '#ef4444' : p.stock_quantity < 10 ? '#eab308' : '#16a34a', fontWeight: 600 }}>{p.stock_quantity}</span>
                </td>
                <td style={{ padding: '12px 16px', fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>{p.sold_count}</td>
                <td style={{ padding: '12px 16px' }}>
                  <span style={{ color: p.is_active ? '#16a34a' : '#6b7280', fontWeight: 600, fontSize: '0.85rem' }}>{p.is_active ? 'Hiển thị' : 'Ẩn'}</span>
                </td>
                <td style={{ padding: '12px 16px' }}>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => openEdit(p)} title="Chỉnh sửa" style={{ background: '#6366f122', color: '#6366f1', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                      <Edit2 size={14} />
                    </button>
                    <button onClick={() => toggleActive(p)} title={p.is_active ? 'Ẩn' : 'Hiện'} style={{ background: '#f59e0b22', color: '#f59e0b', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                      {p.is_active ? <EyeOff size={14} /> : <Eye size={14} />}
                    </button>
                    <button onClick={() => deleteProduct(p.slug)} title="Xóa" style={{ background: '#ef444422', color: '#ef4444', border: 'none', borderRadius: 6, padding: '5px 8px', cursor: 'pointer' }}>
                      <Trash2 size={14} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ padding: '12px 16px', color: 'var(--color-text-muted)', fontSize: '0.8rem', borderTop: '1px solid var(--color-border)' }}>Tổng: {products.length} sản phẩm</div>
      </div>

      {/* Edit Modal */}
      {editModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 999, overflowY: 'auto' }}>
          <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: 32, minWidth: 480, maxWidth: 600, width: '90%', margin: '20px auto' }}>
            <h3 style={{ marginBottom: 20 }}>Chỉnh sửa: {editModal.name}</h3>
            <form onSubmit={saveEdit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14 }}>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Tên sản phẩm</label>
                <input value={editForm.name} onChange={e => setEditForm(f => ({ ...f, name: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Giá bán</label>
                <input type="number" value={editForm.price} onChange={e => setEditForm(f => ({ ...f, price: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Giá gốc</label>
                <input type="number" value={editForm.compare_price} onChange={e => setEditForm(f => ({ ...f, compare_price: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Tồn kho</label>
                <input type="number" value={editForm.stock_quantity} onChange={e => setEditForm(f => ({ ...f, stock_quantity: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>Danh mục</label>
                <select value={editForm.category_slug} onChange={e => setEditForm(f => ({ ...f, category_slug: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
                  {categories.map(c => <option key={c.slug} value={c.slug}>{c.name}</option>)}
                </select>
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 6 }}>URL Hình ảnh chính</label>
                <input value={editForm.image_url} onChange={e => setEditForm(f => ({ ...f, image_url: e.target.value }))}
                  style={{ width: '100%', padding: '9px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
              </div>
              <div style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: '0.9rem' }}>
                  <input type="checkbox" checked={editForm.is_active} onChange={e => setEditForm(f => ({ ...f, is_active: e.target.checked }))} />
                  Hiển thị sản phẩm
                </label>
              </div>
              <div style={{ gridColumn: '1 / -1', display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 4 }}>
                <button type="button" onClick={() => setEditModal(null)} style={{ padding: '10px 20px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', cursor: 'pointer' }}>Hủy</button>
                <button type="submit" style={{ padding: '10px 20px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>Lưu</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </AdminLayout>
  );
}
