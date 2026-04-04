import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { clearAuth, authFetch, API, BASE_URL, isLoggedIn } from '../../utils/auth';

const PLAN_COLORS = {
  light: '#b388ff', regular: '#40c4ff', standard: '#00e676',
  pro: '#ff9800', max: '#ff5252'
};

const RISK_MAP = {
  'GREEN': { color: '#00e676', bg: 'bg-[#00e676]/10', border: 'border-[#00e676]/30', label: 'LOW RISK' },
  'YELLOW': { color: '#ffd700', bg: 'bg-[#ffd700]/10', border: 'border-[#ffd700]/30', label: 'MODERATE' },
  'RED': { color: '#ff5252', bg: 'bg-[#ff5252]/10', border: 'border-[#ff5252]/30', label: 'HIGH RISK' },
  'BLACK': { color: '#1a1f2e', bg: 'bg-[#1a1f2e]/40', border: 'border-white/20', label: 'EXTREME' }
};

const getRiskLevel = (score) => {
  if (score <= 30) return 'GREEN';
  if (score <= 60) return 'YELLOW';
  if (score <= 80) return 'RED';
  return 'BLACK';
};

function ScoreGauge({ score }) {
  const level = getRiskLevel(score);
  const meta = RISK_MAP[level];
  const color = meta.color;
  const pct = (score / 100) * 283;
  return (
    <div className="relative flex items-center justify-center">
      <svg width="110" height="110" viewBox="0 0 100 100">
        <circle cx="50" cy="50" r="45" fill="none" stroke="#1a1f2e" strokeWidth="6" />
        <circle
          cx="50" cy="50" r="45" fill="none" stroke={color} strokeWidth="6"
          strokeDasharray={`${pct} 283`} strokeLinecap="round" transform="rotate(-90 50 50)"
          className="transition-all duration-1000"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-black text-white leading-none">{score}</span>
        <span className="text-[7px] text-gray-500 uppercase mt-1 tracking-widest font-black">SafarScore™</span>
      </div>
    </div>
  );
}

export default function WorkerActive() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [traceLog, setTraceLog] = useState([]);
  const [lastUpdated, setLastUpdated] = useState('');
  const [showSummary, setShowSummary] = useState(false);
  const [payouts, setPayouts] = useState([]);
  const [alerts, setAlerts] = useState([]);

  const fetchDashboard = async (workerId) => {
    try {
      const res = await authFetch(`${BASE_URL}/worker/dashboard_details?worker_id=${workerId}`);
      if (res.ok) {
        const payload = await res.json();
        setData(payload);
        setLastUpdated(new Date().toLocaleTimeString('en-IN'));
        
        // Handle Alerts based on score
        if (payload.safar_score.score >= 60) {
            setAlerts(prev => [{ id: Date.now(), type: 'payout', text: 'TRIGGER FIRED: Payout incoming!' }, ...prev].slice(0, 3));
        } else if (payload.safar_score.score >= 45) {
            setAlerts(prev => [{ id: Date.now(), type: 'warning', text: 'RISK ALERT: 48-hr advance warning!' }, ...prev].slice(0, 3));
        }
      }
      
      const pres = await authFetch(`${BASE_URL}/worker/payouts?worker_id=${workerId}`);
      if (pres.ok) {
        const pdata = await pres.json();
        setPayouts(pdata.payouts);
      }
    } catch (e) {
      console.error("Dashboard detail sync failed", e);
    }
  };

  useEffect(() => {
    if (!isLoggedIn()) { navigate('/worker/login'); return; }
    
    // Initial fetch to get worker ID from /me (Auth URL)
    authFetch(`${API}/me`).then(res => res.json()).then(me => {
      fetchDashboard(me.worker_id);
      setLoading(false);
      
      const iv = setInterval(() => fetchDashboard(me.worker_id), 15000);
      return () => clearInterval(iv);
    }).catch(() => navigate('/worker/login'));
  }, [navigate]);

  const triggerScenario = async (scenario) => {
    if (!data) return;
    const { worker, plan } = data;
    
    setTraceLog(prev => [{ time: new Date().toLocaleTimeString(), text: `Initiating ${scenario.toUpperCase()} validation...`, type: 'info' }, ...prev]);

    try {
      // 1. Update zone score first
      await fetch(`http://localhost:8000/api/demo/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, zone_id: worker.zone })
      });

      // 2. Perform parametric payout calculation
      const res = await fetch(`http://localhost:8000/api/payout/calculate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          worker_id: worker.id,
          scenario: scenario,
          peb_weekly: Math.round(plan.max_payout / (plan.coverage_ratio || 0.7)),
          actual_earned: 300, 
          coverage_ratio: plan.coverage_ratio
        })
      });
      const result = await res.json();
      
      if (result.status === 'approved' || result.status === 'pending_fast_track') {
        setTraceLog(prev => [{ 
            time: new Date().toLocaleTimeString(), 
            text: `💰 PAYOUT APPROVED!`, 
            type: 'success',
            details: `Disruption confirmed · ${result.math.signals_confirmed}/3 signals matched`,
            payout: result.payout_amount,
            math: result.math,
            bps: result.bps_score,
            signals: [
                { name: 'Signal 1', label: 'External (Rain/AQI)', status: 'match' },
                { name: 'Signal 2', label: 'Presence (BPS)', status: result.bps_score >= 50 ? 'match' : 'fail' },
                { name: 'Signal 3', label: 'Platform (Demand)', status: result.math.signals_confirmed === 3 ? 'match' : 'fail' }
            ]
        }, ...prev]);
      } else if (result.status === 'flagged' || (result.status === 'rejected' && scenario === 'spoofer')) {
        setTraceLog(prev => [{ 
            time: new Date().toLocaleTimeString(), 
            text: `🚫 FRAUD BLOCKED`, 
            type: 'error',
            details: `GPS spoof detected. BPS: ${result.bps_score || 0}. Hard block. ₹0 payout. Logged.`,
            bps: result.bps_score || 0,
            note: result.math?.signals_confirmed === 1 ? 'Failed Signal 2 & 3' : 'BPS below security threshold'
        }, ...prev]);
      }

      // Refresh data to show trigger status
      fetchDashboard(worker.id);
    } catch (e) {
      setTraceLog(prev => [{ time: new Date().toLocaleTimeString(), text: `Connection unstable. Payout logic delayed.`, type: 'error' }, ...prev]);
    }
  };

  const handleShiftToggle = async () => {
    if (!data) return;
    const workerId = data.worker.id;
    const endpoint = data.shift.active ? '/worker/shift/end' : '/worker/shift/start';
    
    try {
        const res = await authFetch(`${BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ worker_id: workerId })
        });
        if (res.ok) {
            fetchDashboard(workerId);
        }
    } catch (e) {
        console.error("Shift toggle failed", e);
    }
  };

  if (loading || !data) return (
    <div className="min-h-screen bg-[#080a0e] flex items-center justify-center text-[#00ffcc] font-mono whitespace-pre text-center">
      <div className="animate-pulse">{"🛡️ SYNCING SHIELD...\nLOCALIZING PARAMETRIC TRIGGERS\nUPDATING SAFARSCORE"}</div>
    </div>
  );

  const { 
    worker = { name: 'Worker', id: '?', zone: '?' }, 
    plan = { tier: 'None', premium: 0, max_hours: 40 }, 
    safar_score = { score: 0, level: 'LOW RISK', trigger: false }, 
    billing = { current_day: '...', next_debit: '...' }, 
    weekly_summary = { hours_covered: 0, max_hours: 40, total_payout_received: 0 }, 
    recent_events = [], 
    shift = { active: false, hours_used: 0 } 
  } = (data || {});

  const isTriggered = safar_score?.trigger || false;
  const riskLevel = getRiskLevel(safar_score?.score || 0);
  const riskMeta = RISK_MAP[riskLevel];
  const planTier = (plan?.tier || 'None').toLowerCase();
  const planColor = PLAN_COLORS[planTier] || '#00ffcc';

  return (
    <div className="min-h-screen bg-[#080a0e] text-white p-4 pb-20 font-sans selection:bg-[#00ffcc]/30">
      <div className="max-w-md mx-auto space-y-6">
        
        {/* Header HUD */}
        <header className="flex items-center justify-between py-2 border-b border-white/5 pb-4">
          <div>
            <h1 className="text-sm text-gray-400 uppercase tracking-tighter font-bold flex items-center gap-2">
               <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
               Good evening, {worker.name.split(' ')[0]}
            </h1>
            <p className="text-[10px] text-gray-500 font-medium mt-1">{worker.zone} · {billing.current_day}, Week 12</p>
          </div>
          <div className="flex gap-2">
            <button 
                onClick={() => setShowSummary(true)}
                className="w-8 h-8 rounded-full bg-white/5 border border-white/10 flex items-center justify-center text-xs"
            >
                📊
            </button>
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-cyan-900 to-blue-900 border border-white/10 flex items-center justify-center text-[10px] font-black">
                {worker.name.charAt(0)}
            </div>
          </div>
        </header>

        {/* Live Alerts HUD */}
        {alerts.length > 0 && (
            <div className="space-y-2">
                {alerts.map(a => (
                    <div key={a.id} className={`p-3 rounded-2xl border flex items-center gap-3 animate-in slide-in-from-right-4 ${a.type === 'payout' ? 'bg-red-500/20 border-red-500/30 text-red-100' : 'bg-amber-500/20 border-amber-500/30 text-amber-100'}`}>
                        <span className="text-lg">{a.type === 'payout' ? '🔥' : '⚡'}</span>
                        <p className="text-[10px] font-black uppercase tracking-widest">{a.text}</p>
                        <button onClick={() => setAlerts(prev => prev.filter(x => x.id !== a.id))} className="ml-auto text-[10px] opacity-50 font-black">✕</button>
                    </div>
                ))}
            </div>
        )}

        {/* SafarScore Main Guard */}
        <div className={`relative overflow-hidden p-6 rounded-3xl border-2 transition-all duration-700 ${riskMeta.bg} ${riskMeta.border}`}>
            {isTriggered && <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-red-500 to-transparent animate-shimmer"></div>}
            
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-[10px] font-black uppercase text-gray-500 tracking-[0.2em] mb-1">SafarScore™</h2>
                    <p className="text-xl font-black">Zone: {worker.zone}</p>
                    <div className={`mt-3 inline-flex items-center px-2 py-0.5 rounded text-[9px] font-black uppercase tracking-widest ${isTriggered ? 'bg-red-500 text-white' : 'bg-gray-800 text-gray-400'}`}>
                        {riskMeta.label}
                    </div>
                </div>
                <ScoreGauge score={safar_score.score} />
            </div>

            {isTriggered && (
                <div className="mt-6 p-4 bg-black/40 rounded-2xl border border-white/5 space-y-3">
                    <p className="text-xs text-[#00ffcc] font-bold flex items-center gap-2">
                        <span className="w-2 h-2 rounded-full bg-[#00ffcc] animate-ping"></span>
                        ⚡ Disruption Detected — Payout Triggered
                    </p>
                    <div className="grid grid-cols-4 gap-2 opacity-80">
                        {['🌧 Rain','💨 AQI','📦 Demand','📍 Presence'].map(s => (
                            <div key={s} className="text-[9px] text-gray-400 text-center py-1 bg-white/5 rounded border border-white/5">{s}</div>
                        ))}
                    </div>
                </div>
            )}
            
            <p className="text-[9px] text-gray-600 mt-4 font-mono text-right uppercase">Updates every 15 min · Last updated just now</p>
        </div>

        {/* MicroShield™ Coverage Live Session */}
        <div className="bg-[#0f1117] rounded-3xl p-6 border border-white/5 shadow-2xl relative overflow-hidden">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-xs font-black uppercase text-gray-500 tracking-widest flex items-center gap-2">
                    <span className="text-[#00ffcc] text-lg">🛡️</span>
                    MicroShield™ Active
                </h3>
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
                    <span className="text-[10px] font-black text-green-500 uppercase">Live Protection</span>
                </div>
            </div>

            <div className="mb-8 space-y-4">
                <div className="flex justify-between items-end text-[10px] text-gray-500 font-black uppercase tracking-widest">
                    <span>Weekly Exposure Clock</span>
                    <span className="text-white">{weekly_summary.hours_covered} / {plan.max_hours} Hours</span>
                </div>
                <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden border border-white/5">
                    <div 
                        className="h-full bg-gradient-to-r from-[#00ffcc] to-blue-500 progress-fill relative"
                        style={{ width: `${weekly_summary.exposure_pct}%` }}
                    >
                        <div className="absolute inset-0 bg-white/20 animate-shimmer"></div>
                    </div>
                </div>
                <p className="text-[9px] text-gray-600 leading-relaxed italic">
                    Why "Micro"? You only pay for these {weekly_summary.hours_covered} hours. 
                    Traditional insurance would charge you 24/7 for {168} hours.
                </p>
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="p-4 bg-gradient-to-br from-white/5 to-transparent rounded-2xl border border-white/5">
                    <p className="text-[9px] text-gray-500 uppercase font-black mb-1">Protected Base (PEB)</p>
                    <p className="text-lg font-black font-mono text-white">₹{weekly_summary.protected_base_hourly || '---'}<span className="text-[10px] text-gray-500 font-normal">/hr</span></p>
                    <p className="text-[8px] text-[#00ffcc] font-bold mt-1 uppercase tracking-tighter">Verified by PEB ML Model</p>
                </div>
                <div className="p-4 bg-gradient-to-br from-green-500/5 to-transparent rounded-2xl border border-green-500/10">
                    <p className="text-[9px] text-green-500 uppercase font-black mb-1">Smart Savings</p>
                    <p className="text-lg font-black font-mono text-[#00ffcc]">₹{weekly_summary.money_saved || '---'}</p>
                    <p className="text-[8px] text-gray-500 font-bold mt-1 uppercase tracking-tighter">Exposure-only Benefit</p>
                </div>
            </div>

            <div className="bg-black/30 p-4 rounded-2xl border border-white/5 mb-8">
               <div className="flex items-start gap-3">
                  <div className="text-xl">💰</div>
                  <div>
                    <h4 className="text-[10px] font-black text-white uppercase tracking-widest leading-none mb-1">How it works</h4>
                    <p className="text-[10px] text-gray-300 font-medium leading-relaxed">
                        You pay <span className="text-white font-bold">₹{plan.premium}</span> to protect <span className="text-white font-bold">{plan.max_hours} hours</span> of your week. 
                        The moment a real external disruption hits — the money comes to you automatically. No forms, no calls, no waiting.
                    </p>
                  </div>
               </div>
            </div>

            {/* Execution Trace (Spec-Accurate Signals) */}
            {traceLog.length > 0 && (
                <div className="mb-6 animate-in slide-in-from-bottom-4 duration-500">
                    {traceLog.slice(0, 1).map((log, i) => (
                        <div key={i} className={`p-4 rounded-2xl border ${log.type === 'success' ? 'bg-[#00ffcc]/5 border-[#00ffcc]/20' : 'bg-red-500/10 border-red-500/20'}`}>
                             <div className="flex items-center gap-3 mb-4">
                                 <span className="text-xl shrink-0">{log.type === 'success' ? '💰' : '🚫'}</span>
                                 <h4 className={`text-xs font-black uppercase ${log.type === 'success' ? 'text-[#00ffcc]' : 'text-red-500'}`}>
                                     {log.text}
                                 </h4>
                             </div>
                             
                             {log.type === 'success' && (
                                <div className="space-y-4">
                                    <p className="text-[10px] text-gray-400 font-medium">{log.details}</p>
                                    <div className="grid grid-cols-3 gap-2">
                                        {(log.signals || []).map(s => (
                                            <div key={s.name} className={`p-2 rounded-lg border text-center ${s.status === 'match' ? 'bg-green-500/10 border-green-500/20 text-green-500' : 'bg-gray-500/5 border-white/5 text-gray-600'}`}>
                                                <div className="text-[8px] font-black uppercase opacity-60 leading-none mb-1">{s.name}</div>
                                                <div className="text-[8px] font-bold truncate leading-none">{s.label}</div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="grid grid-cols-2 gap-y-1 text-[10px] font-mono border-t border-white/5 pt-3">
                                         <div className="text-gray-500 uppercase">PEB (expected)</div><div className="text-right text-gray-300">₹{log.math.peb_expected}</div>
                                         <div className="text-gray-500 uppercase">Actual earned</div><div className="text-right text-gray-300">₹{log.math.actual_earned}</div>
                                         <div className="text-gray-500 uppercase pt-1 font-black">Income gap</div><div className="text-right pt-1 text-red-400 font-black">₹{log.math.income_gap}</div>
                                         <div className="text-gray-500 uppercase underline decoration-[#00ffcc]/50">Coverage ({Math.round(log.math.coverage_ratio_used*100)}%)</div><div className="text-right text-gray-300">× {log.math.coverage_ratio_used}</div>
                                         <div className="text-gray-500 uppercase">Confidence ({log.math.signals_confirmed}/3)</div><div className="text-right text-gray-300">× {log.math.confidence_score}</div>
                                         <div className="text-[#00ffcc] font-black text-xs pt-2 border-t border-[#00ffcc]/30">PIN Payout</div><div className="text-right text-[#00ffcc] font-black text-xs pt-2 border-t border-[#00ffcc]/30">₹{log.payout}</div>
                                    </div>
                                    <div className="flex items-center justify-between mt-2 px-1">
                                        <div className="text-[9px] font-black text-[#00ffcc] flex items-center gap-1">
                                            <span className="w-1.5 h-1.5 rounded-full bg-[#00ffcc] animate-pulse"></span>
                                            SENT TO PHONEPE · UPI
                                        </div>
                                        <div className="text-[9px] text-gray-500 font-mono">22 min · ref_sz99</div>
                                    </div>
                                </div>
                             )}

                             {log.type === 'error' && (
                                 <div className="space-y-3">
                                     <p className="text-[10px] text-red-500/80 font-bold leading-relaxed">{log.details}</p>
                                     <div className="flex items-center justify-between text-[9px] font-black uppercase tracking-widest text-[#5a6070] border-t border-white/5 pt-3">
                                         <span>Security Log</span>
                                         <span className="text-red-500">BPS: {log.bps} / 100</span>
                                     </div>
                                 </div>
                             )}
                        </div>
                    ))}
                </div>
            )}

            <button 
                onClick={handleShiftToggle}
                className={`w-full active:scale-95 border-2 font-black py-4 rounded-2xl flex items-center justify-center gap-3 transition-all duration-300 ${shift.active ? 'bg-white/5 border-red-500/30 text-white' : 'bg-gradient-to-r from-[#00ffcc] to-blue-500 border-transparent text-black'}`}
            >
                <span className={`w-3 h-3 rounded-sm ${shift.active ? 'bg-red-600' : 'bg-black animate-pulse'}`}></span>
                <span>{shift.active ? 'End Shift' : 'Start Shift'}</span>
            </button>
        </div>

        {/* Payout History Section */}
        <div className="bg-[#0f1117] rounded-3xl p-6 border border-white/5 shadow-2xl">
            <h3 className="text-[10px] font-black uppercase text-gray-500 tracking-[0.2em] mb-4">Payout History</h3>
            {payouts.length > 0 ? (
                <div className="space-y-3">
                    {payouts.map(p => (
                        <div key={p.id} className="flex items-center justify-between p-3 bg-white/5 rounded-2xl border border-white/5">
                            <div>
                                <p className="text-[10px] text-white font-black uppercase tracking-widest">{p.reason}</p>
                                <p className="text-[8px] text-gray-500 font-mono mt-0.5">{new Date(p.timestamp).toLocaleDateString()} · {Math.round(p.confidence * 100)}% Confidence</p>
                            </div>
                            <div className="text-right">
                                <p className="text-xs font-black text-[#00ffcc]">₹{p.amount}</p>
                                <p className="text-[7px] text-gray-600 font-black uppercase">Verified</p>
                            </div>
                        </div>
                    ))}
                </div>
            ) : (
                <div className="py-8 text-center border-2 border-dashed border-white/5 rounded-2xl">
                    <p className="text-[10px] text-gray-600 font-black uppercase tracking-widest">No payouts yet</p>
                </div>
            )}
        </div>

        {/* Weekly Summary Live Card */}
        <div className="bg-gradient-to-br from-[#1a1f2e] to-[#0f1117] rounded-3xl p-6 border border-white/10 shadow-xl">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xs font-black uppercase text-gray-500 tracking-widest mb-1">📊 This Week's Summary</h3>
                    <p className="text-[10px] text-gray-600">Syncing with Autopay Cycle</p>
                </div>
                <div className="px-3 py-1 bg-green-500/10 text-green-500 rounded-full border border-green-500/20 text-[9px] font-black uppercase tracking-tighter">
                    {billing.next_debit.split('T')[0]} · 6:00 AM
                </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-black/30 rounded-2xl border border-white/5">
                    <p className="text-[9px] text-gray-500 uppercase font-black mb-1">Premium Paid</p>
                    <p className="text-lg font-black font-mono text-white">₹{weekly_summary.premium_paid}</p>
                </div>
                <div className="p-4 bg-black/30 rounded-2xl border border-white/5">
                    <p className="text-[9px] text-gray-500 uppercase font-black mb-1">Payouts Received</p>
                    <p className="text-lg font-black font-mono text-[#00ffcc]">₹{weekly_summary.total_payout_received + (traceLog.filter(t=>t.type==='success')[0]?.payout||0)}</p>
                </div>
                <div className="p-4 bg-black/30 rounded-2xl border border-white/5">
                    <p className="text-[9px] text-gray-500 uppercase font-black mb-1">Hours Worked</p>
                    <p className="text-lg font-black font-mono text-white">{weekly_summary.hours_covered}</p>
                </div>
                <div className="p-4 bg-black/30 rounded-2xl border border-white/5">
                    <p className="text-[9px] text-gray-500 uppercase font-black mb-1">Disruptions</p>
                    <p className="text-lg font-black font-mono text-amber-400">{weekly_summary.disruptions_count || 0}</p>
                </div>
            </div>
            
            <div className="mt-6 flex items-center justify-between text-[11px] text-gray-400 font-black border-t border-white/10 pt-4 uppercase">
                <span>Net Position This Week</span>
                <span className={weekly_summary.net_position >= 0 ? 'text-green-500 text-lg' : 'text-red-400 text-lg'}>
                    {weekly_summary.net_position >= 0 ? '+' : ''}₹{weekly_summary.net_position}
                </span>
            </div>
        </div>

        {/* Presentation Trigger Controls */}
        <section className="space-y-4">
            <div className="flex items-center justify-between px-2">
                <h4 className="text-[10px] font-black uppercase text-gray-600 tracking-widest">Demo Scenarios</h4>
                <span className="text-[8px] bg-[#00ffcc]/10 text-[#00ffcc] px-2 py-0.5 rounded uppercase font-black tracking-widest border border-[#00ffcc]/20">Logic Verified</span>
            </div>
            <div className="grid grid-cols-2 gap-3">
                <button onClick={() => triggerScenario('rain')} className="bg-[#1a1f2e] hover:bg-blue-600/20 border border-white/5 p-4 rounded-2xl text-left transition-all active:scale-95 group">
                    <div className="text-xl mb-2 group-hover:scale-110 transition-transform">🌧</div>
                    <div className="text-xs font-black uppercase">Heavy Rain</div>
                </button>
                <button onClick={() => triggerScenario('flood')} className="bg-[#1a1f2e] hover:bg-red-600/20 border border-white/5 p-4 rounded-2xl text-left transition-all active:scale-95 group">
                    <div className="text-xl mb-2 group-hover:scale-110 transition-transform">🌊</div>
                    <div className="text-xs font-black uppercase">Flash Flood</div>
                </button>
                <button onClick={() => triggerScenario('spoofer')} className="bg-[#1a1f2e] hover:bg-yellow-600/20 border border-white/5 p-4 rounded-2xl text-left transition-all active:scale-95 group">
                    <div className="text-xl mb-2 group-hover:scale-110 transition-transform">🚫</div>
                    <div className="text-xs font-black uppercase">GPS Spoofer</div>
                </button>
                <button onClick={() => triggerScenario('normal')} className="bg-[#1a1f2e] hover:bg-green-600/20 border border-white/5 p-4 rounded-2xl text-left transition-all active:scale-95 group">
                    <div className="text-xl mb-2 group-hover:scale-110 transition-transform">✅</div>
                    <div className="text-xs font-black uppercase">Reset Normal</div>
                </button>
            </div>
        </section>

        {/* Guidewire Hackathon Branding Footer */}
        <div className="pt-24 pb-12 flex flex-col items-center gap-8 group">
            <div className="text-[11px] font-black text-gray-400 uppercase tracking-[0.4em] opacity-70">Official Entry for</div>
            <div className="h-16 w-full flex items-center justify-center overflow-hidden">
                <img src="/guidewire_premium.png" alt="Guidewire" className="h-24 w-full object-contain opacity-90 group-hover:opacity-100 transition-all brightness-150 scale-[2.5]" />
            </div>
            <div className="text-[11px] font-black text-[#00ffcc] tracking-[0.3em] uppercase border-t-2 border-white/10 pt-4 mt-4">DEVTRAILS 2026 HACKATHON</div>
        </div>

        {/* Mobile Navigation Spacer */}
        <div className="h-10"></div>
        
      </div>

      {/* Floating Bottom Navigation */}
      <nav className="fixed bottom-0 left-0 w-full bg-[#0d1117]/80 backdrop-blur-xl border-t border-white/5 px-6 py-4 flex justify-around items-center">
            <div className="text-gray-600 text-xl cursor-not-allowed">🏠</div>
            <div className="text-[#00ffcc] text-xl cursor-pointer" onClick={() => navigate('/worker/active')}>🛡️</div>
            <div className="text-gray-600 text-xl cursor-not-allowed">📜</div>
            <div className="text-gray-600 text-xl cursor-pointer hover:text-red-500" onClick={() => { clearAuth(); navigate('/worker/login'); }}>🚪</div>
      </nav>

      {/* Weekly Summary Modal (Sunday 8PM Logic) */}
      {showSummary && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-[#080a0e]/95 backdrop-blur-md animate-in fade-in duration-500">
              <div className="w-full max-w-sm bg-[#0f1117] border border-white/10 rounded-[3rem] p-8 shadow-[0_0_100px_rgba(0,255,204,0.1)] relative">
                  <div className="absolute -top-10 left-1/2 -translate-x-1/2 w-20 h-20 bg-gradient-to-tr from-[#00ffcc] to-blue-500 rounded-3xl flex items-center justify-center text-3xl shadow-2xl">
                      📊
                  </div>
                  
                  <div className="text-center mt-6 mb-8">
                      <h2 className="text-xl font-black text-white">Your Weekly Summary</h2>
                      <p className="text-[10px] text-gray-500 font-black uppercase tracking-widest mt-2">{weekly_summary.week_range}</p>
                  </div>

                  <div className="space-y-4 mb-8">
                      <div className="flex justify-between items-center p-4 bg-white/5 rounded-2xl border border-white/5">
                          <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Premium Paid</span>
                          <span className="text-sm font-black text-white">₹{weekly_summary.premium_paid}</span>
                      </div>
                      <div className="flex justify-between items-center p-4 bg-white/5 rounded-2xl border border-white/5">
                          <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Payouts Received</span>
                          <span className="text-sm font-black text-[#00ffcc]">₹{weekly_summary.payouts_received}</span>
                      </div>
                      <div className="flex justify-between items-center p-4 bg-white/5 rounded-2xl border border-white/5">
                          <span className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Hours Covered</span>
                          <span className="text-sm font-black text-white">{weekly_summary.hours_covered} hrs</span>
                      </div>
                      <div className="flex justify-between items-center p-4 bg-gradient-to-r from-[#00ffcc]/10 to-transparent rounded-2xl border border-[#00ffcc]/20">
                          <span className="text-[10px] text-[#00ffcc] font-black uppercase tracking-widest font-black">Net Position</span>
                          <span className="text-lg font-black text-[#00ffcc]">₹{weekly_summary.net_position}</span>
                      </div>
                  </div>

                  <button 
                    onClick={() => setShowSummary(false)}
                    className="w-full bg-white text-black font-black py-4 rounded-2xl hover:scale-105 transition-transform"
                  >
                      BACK TO HUD
                  </button>
              </div>
          </div>
      )}
    </div>
  );
}
