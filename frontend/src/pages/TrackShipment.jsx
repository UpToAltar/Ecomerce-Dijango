import React, { useState } from 'react';
import axios from 'axios';
import { Search, Truck, Package, Clock, CheckCircle, AlertCircle, ChevronLeft } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API = 'http://localhost:8000/api';

export default function TrackShipment() {
  const navigate = useNavigate();
  const [trackingNumber, setTrackingNumber] = useState('');
  const [shipment, setShipment] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const getStatusInfo = (status) => {
    switch(status) {
      case 'pending': return { text: 'Chờ xử lý', color: '#eab308', icon: <Clock size={20} />, pct: 10 };
      case 'picked_up': return { text: 'Đã lấy hàng', color: '#3b82f6', icon: <Package size={20} />, pct: 30 };
      case 'in_transit': return { text: 'Đang vận chuyển', color: '#8b5cf6', icon: <Truck size={20} />, pct: 55 };
      case 'out_for_delivery': return { text: 'Đang giao hàng', color: '#f59e0b', icon: <Truck size={20} />, pct: 80 };
      case 'delivered': return { text: 'Đã giao thành công', color: '#16a34a', icon: <CheckCircle size={20} />, pct: 100 };
      case 'failed': return { text: 'Giao hàng thất bại', color: '#dc2626', icon: <AlertCircle size={20} />, pct: 80 };
      case 'returned': return { text: 'Đã hoàn trả', color: '#6b7280', icon: <Package size={20} />, pct: 100 };
      default: return { text: status || 'Không rõ', color: '#6b7280', icon: <Clock size={20} />, pct: 0 };
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!trackingNumber.trim()) return;
    setError('');
    setShipment(null);
    setLoading(true);
    try {
      const res = await axios.get(`${API}/shipping/track/${trackingNumber.trim()}/`);
      setShipment(res.data);
    } catch (err) {
      setError('Không tìm thấy đơn vận chuyển với mã này.');
    } finally {
      setLoading(false);
    }
  };

  const statusInfo = shipment ? getStatusInfo(shipment.status) : null;

  return (
    <div className="container" style={{ padding: '40px 20px', maxWidth: '700px' }}>
      <button className="btn btn-outline" onClick={() => navigate(-1)} style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '6px', border: 'none', paddingLeft: 0 }}>
        <ChevronLeft size={18} /> Quay lại
      </button>

      <div style={{ textAlign: 'center', marginBottom: '32px' }}>
        <Truck size={48} style={{ color: 'var(--color-primary)', marginBottom: '12px' }} />
        <h2 style={{ marginBottom: '8px' }}>Tra cứu vận đơn</h2>
        <p style={{ color: 'var(--color-text-muted)' }}>Nhập mã vận đơn để theo dõi trạng thái giao hàng</p>
      </div>

      <form onSubmit={handleSearch} style={{ display: 'flex', gap: '12px', marginBottom: '32px' }}>
        <input
          type="text"
          value={trackingNumber}
          onChange={e => setTrackingNumber(e.target.value)}
          placeholder="Nhập mã vận đơn (VD: SHP...)"
          style={{
            flex: 1, padding: '14px 16px', borderRadius: '10px',
            border: '1px solid var(--color-border)', background: 'var(--color-surface)',
            color: 'var(--color-text)', fontSize: '1rem', fontFamily: 'monospace',
          }}
        />
        <button type="submit" className="btn btn-primary" disabled={loading} style={{ padding: '14px 24px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Search size={18} />
          {loading ? 'Đang tìm...' : 'Tra cứu'}
        </button>
      </form>

      {error && (
        <div style={{ padding: '16px', background: '#fee2e2', borderRadius: '8px', color: '#dc2626', textAlign: 'center', marginBottom: '24px' }}>
          {error}
        </div>
      )}

      {shipment && (
        <div>
          {/* Status header */}
          <div className="product-card" style={{ padding: '24px', marginBottom: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>Mã vận đơn</div>
                <div style={{ fontWeight: 700, fontSize: '1.2rem', fontFamily: 'monospace' }}>{shipment.tracking_number}</div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: statusInfo.color, fontWeight: 700, fontSize: '1rem' }}>
                {statusInfo.icon} {statusInfo.text}
              </div>
            </div>

            {/* Progress bar */}
            <div style={{ height: '6px', background: 'var(--color-border)', borderRadius: '3px', overflow: 'hidden', marginBottom: '12px' }}>
              <div style={{
                height: '100%', width: `${statusInfo.pct}%`,
                background: statusInfo.color, borderRadius: '3px',
                transition: 'width 0.5s',
              }}></div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
              <span>Đơn vị: {shipment.carrier}</span>
              {shipment.order_number && <span>Đơn hàng: #{shipment.order_number}</span>}
            </div>
          </div>

          {/* Timeline */}
          <div className="product-card" style={{ padding: '24px' }}>
            <h3 style={{ marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Clock size={18} /> Lịch sử vận chuyển
            </h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0' }}>
              {shipment.tracking_events?.map((t, i) => (
                <div key={t.id || i} style={{ display: 'flex', gap: '16px', position: 'relative', paddingBottom: i < shipment.tracking_events.length - 1 ? '24px' : '0' }}>
                  {i < shipment.tracking_events.length - 1 && (
                    <div style={{ position: 'absolute', left: '7px', top: '18px', bottom: '0', width: '2px', background: 'var(--color-border)' }}></div>
                  )}
                  <div style={{
                    width: '16px', height: '16px', borderRadius: '50%', flexShrink: 0,
                    background: i === 0 ? 'var(--color-primary)' : 'var(--color-border)',
                    marginTop: '2px', position: 'relative', zIndex: 1,
                    border: i === 0 ? '3px solid rgba(59,130,246,0.3)' : 'none',
                  }}></div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600 }}>{t.status}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginTop: '2px' }}>
                      {new Date(t.created_at).toLocaleString('vi-VN')}
                      {t.location && ` - ${t.location}`}
                    </div>
                    {t.note && <div style={{ fontSize: '0.85rem', marginTop: '4px', color: 'var(--color-text-secondary)' }}>{t.note}</div>}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
