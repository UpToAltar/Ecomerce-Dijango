import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    const success = await login(email, password);
    if (success) {
      navigate('/');
    } else {
      alert("Login failed! Ensure backend auth-service is running.");
      // For demo fallback:
      login(email, password); navigate('/');
    }
  };

  return (
    <div className="container" style={{ display: 'flex', justifyContent: 'center', padding: '80px 20px' }}>
      <div className="product-card" style={{ maxWidth: '400px', width: '100%', padding: '32px' }}>
        <h2 style={{ marginBottom: '24px', textAlign: 'center' }}>Welcome Back</h2>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Email</label>
            <input 
              type="email" 
              required
              value={email}
              onChange={e => setEmail(e.target.value)}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
            />
          </div>
          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '0.9rem' }}>Password</label>
            <input 
              type="password" 
              required
              value={password}
              onChange={e => setPassword(e.target.value)}
              style={{ width: '100%', padding: '10px', borderRadius: '6px', border: '1px solid var(--color-border)' }}
            />
          </div>
          <button type="submit" className="btn btn-primary" style={{ marginTop: '12px' }}>
            Sign In
          </button>
        </form>
        <p style={{ marginTop: '24px', textAlign: 'center', fontSize: '0.9rem', color: 'var(--color-text-secondary)' }}>
          Don't have an account? <Link to="/register" style={{ fontWeight: 600 }}>Create one</Link>
        </p>
      </div>
    </div>
  );
}
