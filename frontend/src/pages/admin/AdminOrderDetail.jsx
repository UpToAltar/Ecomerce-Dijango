import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { ChevronLeft, Truck, Package, Clock, CheckCircle, AlertCircle } from 'lucide-react';
import AdminLayout from '../../components/admin/AdminLayout';
import { useNavigate, useParams } from 'react-router-dom';

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

export default function AdminOrderDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [order, setOrder] = useState(null);
  const [shipment, setShipment] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [newStatus, setNewStatus] = useState('');
  const [trackingNote, setTrackingNote] = useState('');
  const [trackingLoc, setTrackingLoc] = useState('');
  const [shipStatusUpdate, setShipStatusUpdate] = useState('');

  const load = async () => {
    setLoading(true);
    try {
      const [orderRes, shipRes] = await Promise.all([
        axios.get(`${API}/orders/${id}/`, { headers: authHeader() }),
        axios.get(`${API}/shipping/order/${id}/`, { headers: authHeader() }).catch(() => ({ data: null })),
      ]);
      setOrder(orderRes.data);
      setNewStatus(orderRes.data.status);
      setShipment(shipRes.data);
      if (shipRes.data?.status) setShipStatusUpdate(shipRes.data.status);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); }, [id]);

  const updateOrderStatus = async () => {
    setUpdatingStatus(true);
    try {
      await axios.put(`${API}/orders/${id}/status/`, { status: newStatus }, { headers: authHeader() });
      load();
    } catch { alert('Cập nhật thất bại'); }
    setUpdatingStatus(false);
  };

  const addTracking = async (e) => {
    e.preventDefault();
    if (!shipment) return;
    try {
      await axios.put(`${API}/shipping/${shipment.id}/status/`, {
        status: shipStatusUpdate, location: trackingLoc, note: trackingNote,
      }, { headers: authHeader() });
      setTrackingNote(''); setTrackingLoc('');
      load();
    } catch { alert('Cập nhật vận đơn thất bại'); }
  };

  const createShipment = async () => {
    try {
      await axios.post(`${API}/shipping/create/`, {
        order_id: id, order_number: order.order_number, shipping_address: order.shipping_address,
      }, { headers: authHeader() });
      load();
    } catch (e) { alert(e.response?.data?.error || 'Tạo vận đơn thất bại'); }
  };

  if (loading) return <AdminLayout title="Chi tiết đơn hàng"><div style={{ padding: 60, textAlign: 'center', color: 'var(--color-text-muted)' }}>Đang tải...</div></AdminLayout>;
  if (!order) return <AdminLayout title="Chi tiết đơn hàng"><div style={{ padding: 60, textAlign: 'center' }}>Không tìm thấy đơn hàng</div></AdminLayout>;

  const addr = order.shipping_address || {};
  const shipStatusColors = { pending: '#eab308', picked_up: '#3b82f6', in_transit: '#8b5cf6', out_for_delivery: '#f59e0b', delivered: '#16a34a', failed: '#ef4444', returned: '#6b7280' };
  const shipStatusLabels = { pending: 'Chờ xử lý', picked_up: 'Đã lấy hàng', in_transit: 'Đang vận chuyển', out_for_delivery: 'Đang giao', delivered: 'Đã giao', failed: 'Thất bại', returned: 'Đã hoàn trả' };

  return (
    <AdminLayout title={`Đơn hàng #${order.order_number}`}>
      <button onClick={() => navigate('/admin/orders')} style={{
        display: 'flex', alignItems: 'center', gap: 6, background: 'none', border: 'none',
        color: 'var(--color-primary)', cursor: 'pointer', marginBottom: 24, padding: 0, fontSize: '0.9rem'
      }}>
        <ChevronLeft size={18} /> Quay lại
      </button>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24 }}>
        {/* Order Info */}
        <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)' }}>
          <h3 style={{ marginBottom: 16 }}>Thông tin đơn hàng</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {[
              ['Mã đơn', order.order_number],
              ['Trạng thái', STATUS_LABELS[order.status] || order.status],
              ['Tổng tiền', VND(order.total_amount)],
              ['Phí ship', VND(order.shipping_fee)],
              ['Phương thức', order.payment_method?.toUpperCase()],
              ['Trạng thái TT', order.payment_status],
              ['Ngày tạo', new Date(order.created_at).toLocaleString('vi-VN')],
            ].map(([k, v]) => (
              <div key={k} style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--color-border)', paddingBottom: 8 }}>
                <span style={{ color: 'var(--color-text-muted)', fontSize: '0.85rem' }}>{k}</span>
                <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{v}</span>
              </div>
            ))}
          </div>

          {/* Update status */}
          <div style={{ marginTop: 20 }}>
            <div style={{ fontSize: '0.85rem', fontWeight: 600, marginBottom: 8 }}>Cập nhật trạng thái</div>
            <div style={{ display: 'flex', gap: 8 }}>
              <select value={newStatus} onChange={e => setNewStatus(e.target.value)}
                style={{ flex: 1, padding: '8px 12px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
                {Object.entries(STATUS_LABELS).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
              </select>
              <button onClick={updateOrderStatus} disabled={updatingStatus}
                style={{ padding: '8px 16px', borderRadius: 8, background: 'var(--color-primary)', color: 'white', border: 'none', cursor: 'pointer', fontWeight: 600 }}>
                {updatingStatus ? '...' : 'Lưu'}
              </button>
            </div>
          </div>
        </div>

        {/* Shipping Address */}
        <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)' }}>
          <h3 style={{ marginBottom: 16 }}>Địa chỉ giao hàng</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, fontSize: '0.9rem' }}>
            <div><strong>{addr.name || addr.full_name || 'N/A'}</strong></div>
            <div style={{ color: 'var(--color-text-muted)' }}>{addr.phone}</div>
            <div style={{ color: 'var(--color-text-muted)' }}>{addr.address}</div>
            <div style={{ color: 'var(--color-text-muted)' }}>{[addr.city, addr.district, addr.ward].filter(Boolean).join(', ')}</div>
          </div>
          {order.note && (
            <div style={{ marginTop: 16, padding: 12, background: '#fef3c7', borderRadius: 8, fontSize: '0.85rem', color: '#92400e' }}>
              Ghi chú: {order.note}
            </div>
          )}
        </div>

        {/* Order Items */}
        <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)', gridColumn: '1 / -1' }}>
          <h3 style={{ marginBottom: 16 }}>Sản phẩm</h3>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                {['Sản phẩm', 'Giá', 'Số lượng', 'Thành tiền'].map(h => (
                  <th key={h} style={{ padding: '8px 12px', textAlign: 'left', fontSize: '0.8rem', color: 'var(--color-text-muted)', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(order.items || []).map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <td style={{ padding: '10px 12px', display: 'flex', alignItems: 'center', gap: 10 }}>
                    {item.product_image && <img src={item.product_image} alt="" style={{ width: 40, height: 40, borderRadius: 6, objectFit: 'cover' }} />}
                    <span style={{ fontSize: '0.85rem', fontWeight: 500 }}>{item.product_name}</span>
                  </td>
                  <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>{VND(item.product_price)}</td>
                  <td style={{ padding: '10px 12px', fontSize: '0.85rem' }}>×{item.quantity}</td>
                  <td style={{ padding: '10px 12px', fontSize: '0.85rem', fontWeight: 700 }}>{VND(item.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Shipment Section */}
        <div style={{ background: 'var(--color-surface-elevated)', borderRadius: 16, padding: '24px', border: '1px solid var(--color-border)', gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
            <h3>Vận đơn</h3>
            {!shipment && order.status === 'shipping' && (
              <button onClick={createShipment} style={{
                padding: '8px 16px', background: 'var(--color-primary)', color: 'white',
                border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600, fontSize: '0.85rem',
              }}>
                + Tạo vận đơn
              </button>
            )}
          </div>

          {!shipment ? (
            <div style={{ color: 'var(--color-text-muted)', textAlign: 'center', padding: 30, fontSize: '0.9rem' }}>
              Chưa có vận đơn. {order.status !== 'shipping' ? 'Chuyển đơn sang trạng thái "Đang giao" để tạo vận đơn.' : ''}
            </div>
          ) : (
            <div>
              <div style={{ display: 'flex', gap: 24, marginBottom: 20, flexWrap: 'wrap' }}>
                {[
                  ['Mã vận đơn', shipment.tracking_number],
                  ['Đơn vị', shipment.carrier],
                  ['Trạng thái', shipStatusLabels[shipment.status] || shipment.status],
                  ['Tạo lúc', new Date(shipment.created_at).toLocaleString('vi-VN')],
                ].map(([k, v]) => (
                  <div key={k}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{k}</div>
                    <div style={{ fontWeight: 700, fontSize: '0.9rem' }}>{v}</div>
                  </div>
                ))}
              </div>

              {/* Update shipment status */}
              <form onSubmit={addTracking} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto auto', gap: 8, marginBottom: 20, alignItems: 'end' }}>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Trạng thái vận đơn</label>
                  <select value={shipStatusUpdate} onChange={e => setShipStatusUpdate(e.target.value)}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)' }}>
                    {Object.entries(shipStatusLabels).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Địa điểm</label>
                  <input value={trackingLoc} onChange={e => setTrackingLoc(e.target.value)} placeholder="VD: Kho Hà Nội"
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', boxSizing: 'border-box' }} />
                </div>
                <div>
                  <label style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)', display: 'block', marginBottom: 4 }}>Ghi chú</label>
                  <input value={trackingNote} onChange={e => setTrackingNote(e.target.value)} placeholder="Ghi chú thêm..."
                    style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid var(--color-border)', background: 'var(--color-surface)', color: 'var(--color-text)', minWidth: 160 }} />
                </div>
                <button type="submit" style={{ padding: '8px 16px', background: '#16a34a', color: 'white', border: 'none', borderRadius: 8, cursor: 'pointer', fontWeight: 600, whiteSpace: 'nowrap' }}>
                  Cập nhật
                </button>
              </form>

              {/* Tracking timeline */}
              <h4 style={{ marginBottom: 12, fontSize: '0.9rem' }}>Lịch sử vận chuyển</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
                {(shipment.tracking_events || []).map((ev, i) => (
                  <div key={ev.id} style={{ display: 'flex', gap: 12, paddingBottom: i < shipment.tracking_events.length - 1 ? 16 : 0, position: 'relative' }}>
                    {i < shipment.tracking_events.length - 1 && (
                      <div style={{ position: 'absolute', left: 7, top: 18, bottom: 0, width: 2, background: 'var(--color-border)' }} />
                    )}
                    <div style={{ width: 16, height: 16, borderRadius: '50%', background: i === 0 ? '#6366f1' : 'var(--color-border)', flexShrink: 0, marginTop: 2, position: 'relative', zIndex: 1, border: i === 0 ? '3px solid rgba(99,102,241,0.3)' : 'none' }} />
                    <div>
                      <div style={{ fontWeight: 600, fontSize: '0.85rem' }}>{ev.status}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                        {new Date(ev.created_at).toLocaleString('vi-VN')}
                        {ev.location && ` — ${ev.location}`}
                      </div>
                      {ev.note && <div style={{ fontSize: '0.8rem', color: 'var(--color-text-secondary)', marginTop: 2 }}>{ev.note}</div>}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </AdminLayout>
  );
}
