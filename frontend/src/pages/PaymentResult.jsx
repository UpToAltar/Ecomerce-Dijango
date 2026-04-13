import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { CheckCircle, XCircle, Clock, ShoppingBag } from 'lucide-react';
import axios from 'axios';

const API = 'http://localhost:8000/api';

export default function PaymentResult() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState('loading'); // loading | success | failed
  const [details, setDetails] = useState({});

  useEffect(() => {
    const verifyPayment = async () => {
      const responseCode = searchParams.get('vnp_ResponseCode');

      if (!responseCode) {
        // No VNPay params (COD or direct navigation)
        setStatus('success');
        setDetails({ method: 'cod', message: 'Đặt hàng thành công!' });
        return;
      }

      try {
        // Send VNPay params to backend for verification
        const params = {};
        searchParams.forEach((val, key) => { params[key] = val; });
        const res = await axios.get(`${API}/payments/vnpay/return/`, { params });

        if (res.data.code === '00') {
          setStatus('success');
          setDetails({ method: 'vnpay', payment_id: res.data.payment_id, message: 'Thanh toán VNPay thành công!' });
        } else {
          setStatus('failed');
          setDetails({ code: res.data.code, message: 'Thanh toán thất bại hoặc bị huỷ.' });
        }
      } catch (err) {
        // If backend already verified, check response code directly
        if (responseCode === '00') {
          setStatus('success');
          setDetails({ method: 'vnpay', message: 'Thanh toán VNPay thành công!' });
        } else {
          setStatus('failed');
          setDetails({ message: 'Không xác minh được thanh toán.' });
        }
      }
    };
    verifyPayment();
  }, [searchParams]);

  if (status === 'loading') {
    return (
      <div className="container" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '100px 20px' }}>
        <div className="spinner" style={{ marginBottom: '24px' }}></div>
        <p>Đang xác minh thanh toán...</p>
      </div>
    );
  }

  return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', padding: '80px 20px' }}>
      <div className="product-card" style={{ maxWidth: '480px', width: '100%', padding: '48px 36px', textAlign: 'center' }}>
        {status === 'success' ? (
          <>
            <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#dcfce7', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <CheckCircle size={44} color="#16a34a" />
            </div>
            <h2 style={{ color: '#16a34a', marginBottom: '12px' }}>Đặt hàng thành công! 🎉</h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: '32px' }}>
              {details.message || 'Đơn hàng của bạn đã được tiếp nhận. Chúng tôi sẽ liên hệ sớm nhất!'}
            </p>
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <Link to="/orders" className="btn btn-primary" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <ShoppingBag size={18} /> Xem đơn hàng
              </Link>
              <Link to="/" className="btn btn-outline">Tiếp tục mua sắm</Link>
            </div>
          </>
        ) : (
          <>
            <div style={{ width: '80px', height: '80px', borderRadius: '50%', background: '#fee2e2', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 24px' }}>
              <XCircle size={44} color="#dc2626" />
            </div>
            <h2 style={{ color: '#dc2626', marginBottom: '12px' }}>Thanh toán thất bại</h2>
            <p style={{ color: 'var(--color-text-secondary)', marginBottom: '32px' }}>
              {details.message || 'Đã có lỗi xảy ra. Vui lòng thử lại hoặc chọn phương thức khác.'}
            </p>
            {details.code && <p style={{ fontSize: '0.85rem', color: 'var(--color-text-muted)', marginBottom: '24px' }}>Mã lỗi: {details.code}</p>}
            <div style={{ display: 'flex', gap: '12px', justifyContent: 'center' }}>
              <button className="btn btn-primary" onClick={() => navigate(-1)}>Thử lại</button>
              <Link to="/" className="btn btn-outline">Về trang chủ</Link>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
