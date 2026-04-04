import React, { useEffect, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

const API = 'http://localhost:8000/api';

function fmtINR(v) {
  if (v >= 100000) return `₹${(v / 100000).toFixed(1)}L`;
  if (v >= 1000)   return `₹${(v / 1000).toFixed(1)}K`;
  return `₹${Math.round(v)}`;
}

function StatCard({ label, value, sub, badge, valueColor = 'text-white' }) {
  return (
    <div className="glass-panel p-5 rounded-2xl border border-white/5 hover:border-[#00ffcc]/30 transition-all">
      <h4 className="text-[10px] text-gray-400 uppercase tracking-[0.2em] mb-2 font-black">{label}</h4>
      <div className="text-3xl font-black mb-1 font-mono tracking-tight">{value}</div>
      <div className="text-[10px] text-gray-500 font-medium">{sub}</div>
      {badge && <div className="mt-2 text-[10px] text-[#00ffcc] font-black uppercase tracking-widest">{badge}</div>}
    </div>
  );
}

export default function Analytics() {
  const [metrics, setMetrics] = useState(null);
  const [zones, setZones] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [fraud, setFraud] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const [mRes, zRes, pRes, fRes] = await Promise.all([
        fetch(`${API}/admin/overview`),
        fetch(`${API}/admin/zone_risk`),
        fetch(`${API}/admin/payout_feed`),
        fetch(`${API}/admin/fraud_feed`)
      ]);
      setMetrics(await mRes.json());
      setZones((await zRes.json()).zones);
      setPayouts((await pRes.json()).payouts);
      setFraud((await fRes.json()).alerts);
      setLoading(false);
    } catch (e) {
      console.error("Dashboard fetch failed", e);
    }
  };

  useEffect(() => {
    fetchData();
    const iv = setInterval(fetchData, 15000);
    return () => clearInterval(iv);
  }, []);

  if (loading || !metrics) return <div className="h-screen flex items-center justify-center text-[#00ffcc] font-mono animate-pulse">BOOTING OPS CONSOLE...</div>;

  const planData = Object.entries(metrics.plans.tier_distribution).map(([name, value]) => ({ name, value }));
  const tierColors = { Light: '#6366f1', Regular: '#00ffcc', Standard: '#f59e0b', Pro: '#e23744', Max: '#a855f7' };

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      
      {/* KPI Cards Row */}
      <div className="grid grid-cols-4 gap-5">
        <StatCard 
            label="Active Workers" 
            value={metrics.workers.active_plans.toLocaleString()} 
            sub={`of ${metrics.workers.total} enrolled`}
        />
        <StatCard 
            label="Payouts Total" 
            value={fmtINR(metrics.payouts.total_inr)} 
            sub={`${metrics.payouts.approved_total} workers paid`}
        />
        <StatCard 
            label="Fraud Alerts" 
            value={metrics.fraud.flagged_alerts} 
            sub={`detected by TrustMesh`}
        />
        <StatCard 
            label="Weekly Revenue" 
            value={fmtINR(metrics.plans.weekly_revenue_inr)} 
            sub="Monday auto-debit"
            badge="Expected: ₹8.4L"
        />
      </div>

      <div className="grid grid-cols-12 gap-6">
        
        {/* Left Column (8 units) */}
        <div className="col-span-8 space-y-6">
            
            {/* Live Zone Scores */}
            <div className="glass-panel rounded-3xl p-6 border border-white/5">
                <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-6">Live Zone Scores — Bengaluru</h3>
                <div className="space-y-5">
                    {zones.map(z => (
                        <div key={z.name} className="flex items-center gap-6">
                            <div className="w-4 h-4 rounded-full flex-shrink-0 animate-pulse" style={{ background: z.score > 60 ? '#ff5252' : z.score > 30 ? '#f59e0b' : '#00ffcc' }}></div>
                            <div className="flex-1 text-sm font-bold text-gray-300">{z.name}</div>
                            <div className="w-48 h-2 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-gradient-to-r from-red-500/50 to-red-500" style={{ width: `${z.score}%`, opacity: z.score > 50 ? 1 : 0.3 }}></div>
                            </div>
                            <div className="w-10 text-right font-mono font-black text-white">{z.score}</div>
                            <div className={`px-3 py-1 rounded text-[9px] font-black uppercase tracking-widest ${z.trigger ? 'bg-red-500/20 text-red-500 border border-red-500/30' : 'bg-green-500/10 text-green-500'}`}>
                                {z.trigger ? 'Payout Active' : 'Monitoring'}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Real-Time Payout Log */}
            <div className="glass-panel rounded-3xl p-6 border border-white/5">
                <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-6">Real-Time Payout Log</h3>
                <div className="space-y-4">
                    {payouts.slice(0, 5).map((p, i) => (
                        <div key={i} className="flex items-center justify-between py-3 border-b border-white/5 last:border-0">
                            <div>
                                <div className="text-sm font-bold text-white">{p.name}</div>
                                <div className="text-[10px] text-gray-500 uppercase tracking-widest mt-1">{p.zone}</div>
                            </div>
                            <div className="text-right">
                                <div className="text-sm font-black text-[#00ffcc]">+{fmtINR(p.amt)}</div>
                                <div className="text-[10px] text-gray-500 font-mono mt-1">{p.time}</div>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>

        {/* Right Column (4 units) */}
        <div className="col-span-4 space-y-6">
            
            {/* Fraud Alerts Feed */}
            <div className="glass-panel rounded-3xl p-6 border border-white/5 h-fit">
                <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-6">Fraud Alerts</h3>
                <div className="space-y-6">
                    {fraud.slice(0, 3).map((f, i) => (
                        <div key={i} className="space-y-2">
                             <div className="flex justify-between items-start">
                                <div className="text-sm font-bold text-red-400">{f.title}</div>
                                <div className="text-[9px] text-gray-500 uppercase font-black">{f.meta}</div>
                             </div>
                             <p className="text-[11px] text-gray-400 leading-relaxed font-medium">{f.detail}</p>
                             <button className="text-[10px] font-black uppercase tracking-widest text-white border border-white/10 px-3 py-1.5 rounded-lg hover:bg-white/5 transition-all">View ring detail ↗</button>
                        </div>
                    ))}
                </div>
            </div>

            {/* Plan Distribution */}
            <div className="glass-panel rounded-3xl p-6 border border-white/5">
                <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-6">Plan Distribution</h3>
                <div className="space-y-4 mb-6">
                    {planData.map(d => (
                        <div key={d.name} className="space-y-1">
                            <div className="flex justify-between text-[11px] font-bold text-gray-400 uppercase tracking-widest">
                                <span>{d.name}</span>
                                <span className="text-white">{d.value}</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${(d.value / 1200) * 100}%`, background: tierColors[d.name] }}></div>
                            </div>
                        </div>
                    ))}
                </div>
                <div className="space-y-3 pt-4 border-t border-white/5">
                    <div className="flex justify-between text-[11px] font-medium">
                        <span className="text-gray-500 uppercase tracking-widest">Weekly revenue</span>
                        <span className="text-white font-black">{fmtINR(metrics.plans.weekly_revenue_inr)}</span>
                    </div>
                    <div className="flex justify-between text-[11px] font-medium">
                        <span className="text-gray-500 uppercase tracking-widest">Payout pool</span>
                        <span className="text-white font-black">{fmtINR(metrics.payouts.total_inr)}</span>
                    </div>
                    <div className="flex justify-between text-[11px] font-medium">
                        <span className="text-gray-500 uppercase tracking-widest">Operating margin</span>
                        <span className="text-green-400 font-black">{fmtINR(metrics.plans.weekly_revenue_inr - metrics.payouts.total_inr)}</span>
                    </div>
                </div>
            </div>

            {/* Weekly Scheduled Tasks */}
            <div className="glass-panel rounded-3xl p-6 border border-white/5 shadow-xl">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em]">Weekly Scheduled Tasks</h3>
                </div>
                <div className="space-y-4">
                    <div className="flex justify-between items-center bg-white/5 p-3 rounded-2xl border border-white/5">
                        <span className="text-[11px] text-gray-400 font-medium tracking-wide">Mon 6AM — auto-debit</span>
                        <span className="px-2 py-0.5 bg-green-500/20 text-green-500 text-[10px] font-black rounded uppercase">Done</span>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-3 rounded-2xl border border-white/5">
                        <span className="text-[11px] text-gray-400 font-medium tracking-wide">Celery score update</span>
                        <div className="flex items-center gap-2">
                             <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                             <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">Running</span>
                        </div>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-3 rounded-2xl border border-white/5">
                        <span className="text-[11px] text-gray-400 font-medium tracking-wide">Ring detector (5-min)</span>
                        <div className="flex items-center gap-2">
                             <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-pulse"></div>
                             <span className="text-[10px] font-black text-green-500 uppercase tracking-widest">Running</span>
                        </div>
                    </div>
                    <div className="flex justify-between items-center bg-white/5 p-3 rounded-2xl border border-white/5">
                        <span className="text-[11px] text-gray-400 font-medium tracking-wide">Sun 8PM — summary push</span>
                        <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest">Scheduled</span>
                    </div>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
}
