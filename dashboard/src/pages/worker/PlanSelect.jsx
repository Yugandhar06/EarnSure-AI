import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Navigate } from 'react-router-dom';
import { getWorker, authFetch, API, isLoggedIn } from '../../utils/auth';

const PLAN_COLORS = { light: '#b388ff', regular: '#40c4ff', standard: '#00e676', pro: '#ff9800', max: '#ff5252' };
const PLAN_ICONS = { light: '🌱', regular: '⚡', standard: '🛡️', pro: '🚀', max: '👑' };

export default function WorkerPlanSelector() {
  const { state } = useLocation();
  const navigate = useNavigate();

  const [analyzing, setAnalyzing] = useState(true);
  const [analysisStep, setAnalysisStep] = useState(0);

  const steps = [
    "🔗 Syncing platform OAuth data...",
    "📂 Fetching 8 weeks of historical slots...",
    "🧠 AI building your PEB (Baseline)...",
    "📊 Calculating personalized premiums...",
    "✨ Generating plan recommendations..."
  ];

  useEffect(() => {
    if (!isLoggedIn()) return;
    let current = 0;
    const iv = setInterval(() => {
      current++;
      if (current >= steps.length) {
        clearInterval(iv);
        setTimeout(() => setAnalyzing(false), 500);
      } else {
        setAnalysisStep(current);
      }
    }, 800);
    return () => clearInterval(iv);
  }, []);

  // Redirect if not logged in
  if (!isLoggedIn()) return <Navigate to="/worker/login" />;

  const worker = getWorker() || {};
  const planData = state?.planData || {};
  const { plans = [], recommended_plan_id = 'standard', multipliers_applied = {}, worker_hours_profile = 40 } = planData;
  const workerName = worker?.name || 'Worker';
  const zone = worker?.zone || 'Unknown Zone';

  const [selectedId, setSelectedId] = useState(recommended_plan_id);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState(null);

  const z = multipliers_applied.zone_risk || 1.0;
  const c = multipliers_applied.claim_history || 1.0;
  const zPct = Math.round((z - 1.0) * 100);
  const cPct = Math.round((c - 1.0) * 100);

  const confirmPlan = async () => {
    setConfirming(true);
    setError(null);
    try {
        const res = await authFetch(`${API}/plan/activate`, {
            method: 'POST',
            body: JSON.stringify({ plan_id: selectedId })
        });
        const data = await res.json();
        
        if (data.status === 'success') {
             navigate('/worker/active');
        } else {
             setError(data.detail || "Failed to activate plan");
        }
    } catch (e) {
        setError("Network error communicating with DB");
    }
    setConfirming(false);
  };

  // Fallback demo plans if backend not called/refreshed page directly
  const displayPlans = plans.length > 0 ? plans : [
    { id: 'light', tier: 'Light', final_premium_inr: 99, base_premium_inr: 99, coverage_ratio_percent: 60, max_coverage_inr: 1000, description: 'Up to 15 hrs/week' },
    { id: 'regular', tier: 'Regular', final_premium_inr: 179, base_premium_inr: 179, coverage_ratio_percent: 65, max_coverage_inr: 2000, description: 'Up to 35 hrs/week' },
    { id: 'standard', tier: 'Standard', final_premium_inr: 249, base_premium_inr: 249, coverage_ratio_percent: 70, max_coverage_inr: 3500, description: 'Up to 55 hrs/week' },
    { id: 'pro', tier: 'Pro', final_premium_inr: 349, base_premium_inr: 349, coverage_ratio_percent: 80, max_coverage_inr: 5000, description: 'Up to 70 hrs/week' },
    { id: 'max', tier: 'Max', final_premium_inr: 449, base_premium_inr: 449, coverage_ratio_percent: 90, max_coverage_inr: 7000, description: 'Unlimited hours' },
  ];

  if (analyzing) return (
    <div style={{ minHeight: '100vh', background: '#080a0e', color: '#00ffcc', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: 20, fontFamily: "'Space Grotesk', sans-serif" }}>
      <div style={{ fontSize: 50, marginBottom: 30 }}>🧠</div>
      <div style={{ fontSize: 24, fontWeight: 900, marginBottom: 10, letterSpacing: 1 }}>SMARTSHIFT<span style={{ color: '#b388ff' }}>+</span> AI</div>
      <div style={{ height: 2, width: 220, background: '#111', borderRadius: 4, overflow: 'hidden', marginBottom: 20, border: '1px solid #222' }}>
         <div style={{ height: '100%', background: '#00ffcc', width: `${((analysisStep+1)/steps.length)*100}%`, transition: 'all 0.5s' }}></div>
      </div>
      <div style={{ fontSize: 13, color: '#5a6070', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 2 }}>{steps[analysisStep]}</div>
      <div style={{ marginTop: 40, color: '#333', fontSize: 10, fontFamily: 'monospace' }}>PROFILER V2.4.9 ACTIVE · EXECUTING K-MEANS</div>
    </div>
  );

  return (
    <div style={{ minHeight: '100vh', background: '#080a0e', fontFamily: "'Space Grotesk', sans-serif", padding: '40px 20px 120px' }}>
      <div style={{ maxWidth: 600, margin: '0 auto' }}>

        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: 8 }}>
          <div style={{ fontSize: 26, fontWeight: 800, color: '#00ffcc' }}>SMARTSHIFT<span style={{ color: '#b388ff' }}>+</span></div>
        </div>
        <div style={{ textAlign: 'center', marginBottom: 36 }}>
          <div style={{ color: 'white', fontSize: 22, fontWeight: 700 }}>Choose Your Weekly Shield</div>
          <div style={{ color: '#5a6070', fontSize: 14, marginTop: 6 }}>Hi {workerName} 👋 — Covering zone: <span style={{ color: '#00ffcc' }}>{zone}</span></div>
          {worker_hours_profile > 0 && (
            <div style={{ color: '#5a6070', fontSize: 13, marginTop: 4 }}>
              Based on your platform history: <strong style={{ color: 'white' }}>{worker_hours_profile} hrs/week</strong>
            </div>
          )}
        </div>

        {/* Pricing Factors */}
        {(z !== 1.0 || c !== 1.0) && (
          <div style={{ background: '#112240', border: '1px solid #233554', borderRadius: 14, padding: '16px 20px', marginBottom: 28 }}>
            <div style={{ color: 'white', fontSize: 14, fontWeight: 700, marginBottom: 10 }}>📊 Pricing Factors Applied to Your Profile</div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
              <span style={{ color: '#8892b0', fontSize: 13 }}>Zone Risk ({zone}):</span>
              <span style={{ color: zPct > 0 ? '#ff5252' : '#00e676', fontWeight: 700, fontSize: 13 }}>
                {zPct > 0 ? `+${zPct}% markup` : `${zPct}% discount`}
              </span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ color: '#8892b0', fontSize: 13 }}>Claim History Factor:</span>
              <span style={{ color: cPct > 0 ? '#ff5252' : '#00e676', fontWeight: 700, fontSize: 13 }}>
                {cPct < 0 ? `${cPct}% loyalty discount` : cPct > 0 ? `+${cPct}% penalty` : 'Clean record'}
              </span>
            </div>
          </div>
        )}

        {/* Error */}
        {error && <div style={{ color: '#ff5252', fontSize: 13, marginBottom: 16, background: '#ff525211', border: '1px solid #ff525222', borderRadius: 8, padding: '8px 12px' }}>{error}</div>}

        {/* Plan Cards */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14, marginBottom: 28 }}>
          {displayPlans.map(p => {
             const isSelected = selectedId === p.id;
             const isAI = p.id === recommended_plan_id;
             const color = PLAN_COLORS[p.id] || '#00e676';
             const icon = PLAN_ICONS[p.id] || '🛡️';
 
             return (
               <div key={p.id} onClick={() => setSelectedId(p.id)} style={{
                 background: isSelected ? `${color}12` : '#0f1117',
                 border: `2px solid ${isSelected ? color : '#22262e'}`,
                 borderRadius: 16, padding: 20, cursor: 'pointer',
                 transition: 'all 0.2s', position: 'relative', overflow: 'hidden',
                 transform: isSelected ? 'scale(1.01)' : 'scale(1)',
                 boxShadow: isSelected ? `0 0 20px ${color}22` : 'none'
               }}>
                 {isAI && (
                   <div style={{
                     position: 'absolute', top: 0, right: 0,
                     background: color, color: '#080a0e', fontSize: 10, fontWeight: 800,
                     padding: '4px 12px', borderBottomLeftRadius: 10
                   }}>AI BEST FIT ✨</div>
                 )}
 
                 <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 14 }}>
                   <div>
                     <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                       <span style={{ fontSize: 20 }}>{icon}</span>
                       <span style={{ color: 'white', fontSize: 20, fontWeight: 700 }}>{p.tier}</span>
                     </div>
                     <div style={{ color: '#5a6070', fontSize: 13, marginTop: 4 }}>{p.description}</div>
                   </div>
                   <div style={{ textAlign: 'right' }}>
                     <div style={{ color: color, fontSize: 26, fontWeight: 800 }}>₹{p.final_premium_inr}</div>
                     <div style={{ color: '#5a6070', fontSize: 11 }}>per week</div>
                   </div>
                 </div>
 
                 <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid #22262e', paddingTop: 12 }}>
                   <div>
                     <div style={{ color: '#5a6070', fontSize: 11 }}>Coverage Ratio</div>
                     <div style={{ color: 'white', fontSize: 14, fontWeight: 700, marginTop: 2 }}>{p.coverage_ratio_percent}% of income gap</div>
                   </div>
                   <div style={{ textAlign: 'right' }}>
                     <div style={{ color: '#5a6070', fontSize: 11 }}>Max Weekly Payout</div>
                     <div style={{ color: color, fontSize: 14, fontWeight: 700, marginTop: 2 }}>₹{p.max_coverage_inr.toLocaleString()}</div>
                   </div>
                 </div>
 
                 {p.final_premium_inr !== p.base_premium_inr && (
                   <div style={{ color: '#5a6070', fontSize: 11, textAlign: 'center', marginTop: 10, fontStyle: 'italic' }}>
                     Base ₹{p.base_premium_inr} → adjusted to ₹{p.final_premium_inr} based on your profile
                   </div>
                 )}
               </div>
             );
           })}
        </div>

        {/* Sticky Confirm Button */}
        <div style={{ position: 'fixed', bottom: 0, left: 0, right: 0, background: '#080a0e', borderTop: '1px solid #22262e', padding: '20px', zIndex: 100 }}>
          <div style={{ maxWidth: 600, margin: '0 auto', display: 'flex', gap: 12, alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <div style={{ color: '#5a6070', fontSize: 12 }}>Selected Plan</div>
              <div style={{ color: 'white', fontWeight: 700 }}>{displayPlans.find(p => p.id === selectedId)?.tier || 'Standard'} — ₹{displayPlans.find(p => p.id === selectedId)?.final_premium_inr || 249}/wk</div>
            </div>
            <button onClick={confirmPlan} disabled={confirming} style={{
              background: '#00ffcc', color: '#080a0e', fontWeight: 800, fontSize: 15,
              padding: '14px 28px', borderRadius: 12, border: 'none', cursor: 'pointer',
              opacity: confirming ? 0.7 : 1, whiteSpace: 'nowrap'
            }}>
              {confirming ? 'Linking UPI...' : '🔗 Set UPI Autopay & Start →'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
