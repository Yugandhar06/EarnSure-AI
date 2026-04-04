import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { saveAuth, API } from '../../utils/auth';

export default function Login() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [form, setForm] = useState({ phone: '', otp: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const sendOTP = async () => {
    if (form.phone.length !== 10) return setError('Enter valid 10-digit number');
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/otp/send`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: form.phone })
      });
      const data = await res.json();
      if (data.status === 'success') setStep(2);
      else setError(data.detail || 'Failed to send OTP');
    } catch { setError('Backend not reachable.'); }
    setLoading(false);
  };

  const verifyOTP = async () => {
    if (form.otp.length !== 6) return setError('Enter 6-digit OTP');
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/otp/verify`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: form.phone, otp: form.otp })
      });
      const data = await res.json();
      if (data.status === 'success') {
          saveAuth(data.token, { worker_id: data.worker_id, phone: form.phone });
          if(data.kyc_verified) {
             navigate('/worker/active'); 
          } else {
             setError("It seems you haven't completed registration.");
          }
      } else setError(data.detail || 'Invalid OTP. Demo OTP is 123456.');
    } catch { setError('Backend error.'); }
    setLoading(false);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#080a0e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Space Grotesk', sans-serif", padding: 20 }}>
      {/* UI Remains the same */}
      <div style={{ width: '100%', maxWidth: 440 }}>

        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: '#00ffcc', letterSpacing: 1 }}>SMARTSHIFT<span style={{ color: '#b388ff' }}>+</span></div>
          <div style={{ color: '#5a6070', fontSize: 13, marginTop: 4 }}>Welcome back, delivery partner</div>
        </div>

        <div style={{ background: '#0f1117', border: '1px solid #22262e', borderRadius: 20, padding: 36 }}>
          {step === 1 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Sign In</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 28 }}>Enter your registered mobile number</p>
              <label style={labelStyle}>Mobile Number</label>
              <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
                <div style={{ ...inputStyle, width: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>+91</div>
                <input style={{ ...inputStyle, flex: 1 }} placeholder="9999999999" maxLength={10}
                  value={form.phone} onChange={e => set('phone', e.target.value.replace(/\D/g, ''))} />
              </div>
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={sendOTP} disabled={loading}>
                {loading ? 'Sending OTP...' : 'Get OTP →'}
              </button>
              <p style={{ color: '#5a6070', fontSize: 13, textAlign: 'center', marginTop: 20 }}>
                New worker? <Link to="/worker/register" style={{ color: '#00ffcc', textDecoration: 'none' }}>Register here</Link>
              </p>
            </>
          )}

          {step === 2 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Enter OTP</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 16 }}>Sent to +91 {form.phone} &nbsp;
                <span style={{ color: '#00ffcc', cursor: 'pointer' }} onClick={() => setStep(1)}>Change</span>
              </p>
              <p style={{ color: '#5a6070', fontSize: 12, marginBottom: 20, background: '#00ffcc11', border: '1px solid #00ffcc22', borderRadius: 8, padding: '8px 12px' }}>
                🔒 Demo OTP: <strong style={{ color: '#00ffcc' }}>123456</strong>
              </p>
              <input style={{ ...inputStyle, letterSpacing: 12, fontSize: 22, textAlign: 'center', marginBottom: 20 }}
                placeholder="------" maxLength={6}
                value={form.otp} onChange={e => set('otp', e.target.value.replace(/\D/g, ''))} />
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={verifyOTP} disabled={loading}>
                {loading ? 'Signing in...' : 'Sign In →'}
              </button>
            </>
          )}
        </div>
        {/* Guidewire Hackathon Branding Footer */}
        <div style={{ marginTop: 100, textAlign: 'center', opacity: 0.9, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20 }}>
            <div style={{ color: '#5a6070', fontSize: 11, fontWeight: 900, textTransform: 'uppercase', letterSpacing: 5 }}>Official Entry for</div>
            <div style={{ height: 60, width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', overflow: 'hidden' }}>
                <img src="/guidewire_premium.png" alt="Guidewire" style={{ height: 30, width: '100%', objectFit: 'contain', filter: 'brightness(1.5) contrast(1.1)', transform: 'scale(3)' }} />
            </div>
            <div style={{ 
                color: '#00ffcc', fontSize: 11, fontWeight: 900, letterSpacing: 4, 
                borderTop: '2px solid #22262e', paddingTop: 16, marginTop: 10 
            }}>DEVTRAILS 2026 HACKATHON</div>
        </div>
      </div>
    </div>
  );
}

const labelStyle = { color: '#8892b0', fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 1, display: 'block', marginBottom: 8 };
const inputStyle = { width: '100%', background: '#161920', border: '1px solid #22262e', borderRadius: 10, padding: '14px 16px', color: 'white', fontSize: 15, outline: 'none', boxSizing: 'border-box', fontFamily: 'inherit' };
const btnStyle = { width: '100%', background: '#00ffcc', color: '#080a0e', fontWeight: 800, fontSize: 15, padding: '16px', borderRadius: 12, border: 'none', cursor: 'pointer' };
const errStyle = { color: '#ff5252', fontSize: 13, marginBottom: 16, background: '#ff525211', border: '1px solid #ff525222', borderRadius: 8, padding: '8px 12px' };
