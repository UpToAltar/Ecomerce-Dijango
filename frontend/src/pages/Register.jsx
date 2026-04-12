import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Register() {
  const [formData, setFormData] = useState({ first_name: '', last_name: '', email: '', password: '' });
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await register(formData);
    if (success) {
      navigate('/');
    } else {
      alert("Registration failed! Check your backend API.");
      navigate('/');
    }
  };

  return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', padding: '80px 20px' }}>
      <div className="product-card" style={{ maxWidth: '450px', width: '100%', padding: '32px' }}>
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Create Account</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'flex', gap: '16px' }}>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>First Name</label>
              <input 
                required value={formData.first_name} 
                onChange={e => setFormData({...formData, first_name: e.target.value})}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
              />
            </div>
            <div style={{ flex: 1 }}>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Last Name</label>
              <input 
                required value={formData.last_name} 
                onChange={e => setFormData({...formData, last_name: e.target.value})}
                style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
              />
            </div>
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Email</label>
            <input 
              type="email" required value={formData.email} 
              onChange={e => setFormData({...formData, email: e.target.value})}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Password</label>
            <input 
              type="password" required value={formData.password} 
              onChange={e => setFormData({...formData, password: e.target.value})}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: '12px' }}>
            Sign Up
          </button>
        </form>
        <p style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          Already have an account? <Link to="/login" style={{ fontWeight: 600 }}>Sign in</Link>
        </p>
      </div>
    </div>
  );
}
