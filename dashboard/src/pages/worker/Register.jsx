import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { saveAuth, API, authFetch, getWorker } from '../../utils/auth';

const ZONES = ['Koramangala', 'HSR Layout', 'Whitefield', 'JP Nagar', 'Indiranagar', 'Malleshwaram', 'BTM Layout', 'Marathahalli'];
const PLATFORMS = ['Swiggy', 'Zomato', 'Dunzo', 'Blinkit'];

export default function Register() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1=Phone, 2=OTP, 3=KYC, 4=Platform
  const [form, setForm] = useState({ phone: '', otp: '', aadhaar: '', name: '', zone: '', platform: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const sendOTP = async () => {
    if (form.phone.length !== 10) return setError('Enter a valid 10-digit number');
    setLoading(true); setError('');
    try {
      const res = await fetch(`${API}/otp/send`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: form.phone })
      });
      const data = await res.json();
      if (data.status === 'success') setStep(2);
      else setError(data.detail || 'Failed to send OTP');
    } catch { setError('Backend not reachable. Make sure server is running.'); }
    setLoading(false);
  };

  const verifyOTP = async () => {
    if (form.otp.length !== 6) return setError('Enter the 6-digit OTP');
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
             navigate('/worker/active'); // Already registered fully
        } else {
             setStep(3); 
        }
      }
      else setError(data.detail || 'Invalid OTP. Try 123456 for demo.');
    } catch { setError('Backend error. Check server.'); }
    setLoading(false);
  };

  const verifyKYC = async () => {
    if (!form.name || form.aadhaar.length !== 12 || !form.zone) return setError('Fill all KYC fields');
    setLoading(true); setError('');
    
    try {
        const res = await authFetch(`${API}/kyc/submit`, {
            method: 'POST',
            body: JSON.stringify({ phone: form.phone, name: form.name, aadhaar: form.aadhaar, zone: form.zone })
        });
        const data = await res.json();
        if(data.status === 'success') {
            setStep(4);
        } else {
            setError(data.detail || 'KYC Failed');
        }
    } catch {
        setError('Error submitting KYC');
    }
    setLoading(false);
  };

  const linkPlatform = async () => {
    if (!form.platform) return setError('Select a platform');
    setLoading(true); setError('');
    try {
      const res = await authFetch(`${API}/oauth/link`, {
        method: 'POST',
        body: JSON.stringify({ platform: form.platform.toLowerCase(), zone_risk: 'medium', claim_history: 'zero_claims' })
      });
      const data = await res.json();
      if (data.status === 'success') {
        const worker = getWorker();
        saveAuth(localStorage.getItem('smartshift_token'), { ...worker, name: form.name, zone: form.zone });
        navigate('/worker/plans', { state: { planData: data.recommended_plan } });
      } else {
          setError(data.detail || 'Failed to link platform');
      }
    } catch { setError('Backend not reachable.'); }
    setLoading(false);
  };

  const steps = ['Phone', 'OTP', 'KYC', 'Platform'];

  return (
    <div style={{ minHeight: '100vh', background: '#080a0e', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: "'Space Grotesk', sans-serif", padding: 20 }}>
      {/*...rest of UI remains identical, only logical parts updated...*/}
      <div style={{ width: '100%', maxWidth: 480 }}>

        {/* Logo */}
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <div style={{ fontSize: 28, fontWeight: 800, color: '#00ffcc', letterSpacing: 1 }}>SMARTSHIFT<span style={{ color: '#b388ff' }}>+</span></div>
          <div style={{ color: '#5a6070', fontSize: 13, marginTop: 4 }}>Worker Protection Platform</div>
        </div>

        {/* Progress Steps */}
        <div style={{ display: 'flex', alignItems: 'center', marginBottom: 36, gap: 0 }}>
          {steps.map((s, i) => (
            <React.Fragment key={s}>
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                <div style={{
                  width: 32, height: 32, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center',
                  background: i + 1 < step ? '#00ffcc' : i + 1 === step ? '#00ffcc22' : '#161920',
                  border: `2px solid ${i + 1 <= step ? '#00ffcc' : '#22262e'}`,
                  color: i + 1 < step ? '#080a0e' : i + 1 === step ? '#00ffcc' : '#5a6070',
                  fontSize: 13, fontWeight: 700, transition: 'all 0.3s'
                }}>
                  {i + 1 < step ? '✓' : i + 1}
                </div>
                <div style={{ color: i + 1 === step ? '#00ffcc' : '#5a6070', fontSize: 11, marginTop: 4 }}>{s}</div>
              </div>
              {i < steps.length - 1 && <div style={{ flex: 2, height: 2, background: i + 1 < step ? '#00ffcc' : '#22262e', marginBottom: 20, transition: 'all 0.3s' }} />}
            </React.Fragment>
          ))}
        </div>

        {/* Card */}
        <div style={{ background: '#0f1117', border: '1px solid #22262e', borderRadius: 20, padding: 36 }}>

          {/* Step 1: Phone */}
          {step === 1 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Create Account</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 28 }}>Enter your mobile number to get started</p>
              <label style={labelStyle}>Mobile Number</label>
              <div style={{ display: 'flex', gap: 10, marginBottom: 20 }}>
                <div style={{ ...inputStyle, width: 60, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>+91</div>
                <input style={{ ...inputStyle, flex: 1 }} placeholder="9999999999" maxLength={10}
                  value={form.phone} onChange={e => set('phone', e.target.value.replace(/\D/g, ''))} />
              </div>
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={sendOTP} disabled={loading}>
                {loading ? 'Sending...' : 'Send OTP →'}
              </button>
              <p style={{ color: '#5a6070', fontSize: 13, textAlign: 'center', marginTop: 20 }}>
                Already registered? <Link to="/worker/login" style={{ color: '#00ffcc', textDecoration: 'none' }}>Sign In</Link>
              </p>
            </>
          )}

          {/* Step 2: OTP */}
          {step === 2 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Verify OTP</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 28 }}>Sent to +91 {form.phone} &nbsp; <span style={{ color: '#00ffcc', cursor: 'pointer' }} onClick={() => setStep(1)}>Change</span></p>
              <p style={{ color: '#5a6070', fontSize: 12, marginBottom: 12, background: '#00ffcc11', border: '1px solid #00ffcc22', borderRadius: 8, padding: '8px 12px' }}>
                🔒 Demo OTP: <strong style={{ color: '#00ffcc' }}>123456</strong>
              </p>
              <label style={labelStyle}>6-Digit OTP</label>
              <input style={{ ...inputStyle, letterSpacing: 12, fontSize: 20, textAlign: 'center', marginBottom: 20 }}
                placeholder="------" maxLength={6}
                value={form.otp} onChange={e => set('otp', e.target.value.replace(/\D/g, ''))} />
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={verifyOTP} disabled={loading}>
                {loading ? 'Verifying...' : 'Verify & Continue →'}
              </button>
            </>
          )}

          {/* Step 3: KYC */}
          {step === 3 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Aadhaar KYC</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 28 }}>Required for IRDAI compliance</p>
              <label style={labelStyle}>Full Name (as on Aadhaar)</label>
              <input style={{ ...inputStyle, marginBottom: 16 }} placeholder="Rajesh Kumar"
                value={form.name} onChange={e => set('name', e.target.value)} />
              <label style={labelStyle}>Aadhaar Number</label>
              <input style={{ ...inputStyle, marginBottom: 16 }} placeholder="1234 5678 9012" maxLength={12}
                value={form.aadhaar} onChange={e => set('aadhaar', e.target.value.replace(/\D/g, ''))} />
              <label style={labelStyle}>Primary Working Zone</label>
              <select style={{ ...inputStyle, marginBottom: 24 }} value={form.zone} onChange={e => set('zone', e.target.value)}>
                <option value="">Select your main zone</option>
                {ZONES.map(z => <option key={z} value={z}>{z}</option>)}
              </select>
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={verifyKYC} disabled={loading}>
                {loading ? 'Verifying KYC...' : 'Confirm KYC →'}
              </button>
            </>
          )}

          {/* Step 4: Platform OAuth */}
          {step === 4 && (
            <>
              <h2 style={{ color: 'white', fontSize: 22, fontWeight: 700, marginBottom: 6 }}>Link Platform</h2>
              <p style={{ color: '#5a6070', fontSize: 14, marginBottom: 28 }}>We analyse your earnings history to recommend the best plan</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 24 }}>
                {PLATFORMS.map(p => (
                  <button key={p} onClick={() => set('platform', p)} style={{
                    padding: '16px 12px', borderRadius: 12, border: `2px solid ${form.platform === p ? '#00ffcc' : '#22262e'}`,
                    background: form.platform === p ? '#00ffcc11' : '#161920',
                    color: form.platform === p ? '#00ffcc' : '#8892b0',
                    fontWeight: 700, fontSize: 14, cursor: 'pointer', transition: 'all 0.2s'
                  }}>{p}</button>
                ))}
              </div>
              {error && <p style={errStyle}>{error}</p>}
              <button style={{ ...btnStyle, opacity: loading ? 0.7 : 1 }} onClick={linkPlatform} disabled={loading}>
                {loading ? 'Analysing Earnings...' : '🔗 Link & Get My Plan →'}
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
const btnStyle = { width: '100%', background: '#00ffcc', color: '#080a0e', fontWeight: 800, fontSize: 15, padding: '16px', borderRadius: 12, border: 'none', cursor: 'pointer', transition: 'all 0.2s' };
const errStyle = { color: '#ff5252', fontSize: 13, marginBottom: 16, background: '#ff525211', border: '1px solid #ff525222', borderRadius: 8, padding: '8px 12px' };
