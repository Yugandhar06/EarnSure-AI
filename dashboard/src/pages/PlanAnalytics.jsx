import React, { useState, useEffect } from 'react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell
} from 'recharts';

const TIER_COLORS = {
  'Light': '#6366f1',
  'Regular': '#00ffcc',
  'Standard': '#f59e0b',
  'Pro': '#e23744',
  'Max': '#a855f7'
};

export default function PlanAnalytics() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchFinanceData = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/admin/plan_analytics');
      if (!res.ok) {
        console.error("Endpoint returned status:", res.status);
        const err = await res.json();
        console.error("Error body:", err);
        throw new Error(`Server error: ${res.status}`);
      }
      const financeData = await res.json();
      console.log("Finance data received:", financeData);
      setData(financeData);
      setLoading(false);
    } catch (e) {
      console.error("Finance fetch error:", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchFinanceData();
    const iv = setInterval(fetchFinanceData, 15000);
    return () => clearInterval(iv);
  }, []);

  if (loading || !data) return <div className="h-screen flex items-center justify-center text-[#00ffcc] font-mono animate-pulse uppercase tracking-[0.2em]">Crunching Financials...</div>;

  const fmtINR = (val) => `₹${Math.round(val).toLocaleString()}`;

  return (
    <div className="space-y-8 animate-fade-in pb-10">
      
      {/* Header */}
      <header>
        <h2 className="text-3xl font-bold text-white tracking-wide">Plan Analytics & Financial Health</h2>
        <p className="text-gray-400 mt-1 text-sm">Revenue pool vs parametric payout exposure</p>
      </header>

      {/* Monday Auto-Debit Alerts */}
      <div className="bg-red-500/10 border border-red-500/20 rounded-3xl p-6">
          <div className="flex items-center gap-3 mb-4">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-ping"></div>
              <h3 className="text-sm font-black text-red-500 uppercase tracking-widest">Active Alerts: Failed Mandates (Monday)</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.failed_mandates.map((a, i) => (
                  <div key={i} className="bg-red-500/5 border border-red-500/10 p-4 rounded-2xl flex items-center justify-between">
                      <div>
                          <div className="text-xs font-bold text-white">{a.name} ({a.id})</div>
                          <div className="text-[10px] text-red-400 font-medium mt-1">{a.reason}</div>
                      </div>
                      <button className="text-[10px] font-black uppercase text-white bg-red-500/20 px-3 py-1.5 rounded-lg active:scale-95 transition-transform">Retry</button>
                  </div>
              ))}
          </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-12 gap-8">
          
          {/* Plan Distribution Bar Chart */}
          <div className="col-span-12 lg:col-span-8 glass-panel rounded-3xl p-8 border border-white/5 bg-[#161616] h-[440px] flex flex-col relative">
              <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-8 shrink-0">Worker Plan Distribution</h3>
              <div className="flex-grow w-full min-h-[300px]">
                  <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={data.tier_distribution} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                          <XAxis dataKey="name" stroke="#444" tick={{ fill: '#888', fontSize: 10, fontWeight: 700 }} axisLine={false} tickLine={false} />
                          <YAxis stroke="#444" tick={{ fill: '#888', fontSize: 10, fontWeight: 700 }} axisLine={false} tickLine={false} />
                          <Tooltip 
                            cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                            contentStyle={{ background: '#111', border: '1px solid #333', borderRadius: '15px' }}
                          />
                          <Bar dataKey="value" radius={[10, 10, 0, 0]} barSize={50}>
                              {data.tier_distribution.map((entry, index) => (
                                  <Cell key={`cell-${index}`} fill={TIER_COLORS[entry.name] || '#00ffcc'} />
                              ))}
                          </Bar>
                      </BarChart>
                  </ResponsiveContainer>
              </div>
          </div>

          {/* Revenue vs Payout Breakdown */}
          <div className="col-span-12 lg:col-span-4 glass-panel rounded-3xl p-8 border border-white/5">
              <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-8">Financial Summary</h3>
              <div className="space-y-8">
                  <div>
                      <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-2">Total Weekly Revenue</div>
                      <div className="text-4xl font-black text-white">{fmtINR(data.financials.total_weekly_revenue)}</div>
                  </div>
                  <div>
                      <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest mb-2">Active Payout Pool</div>
                      <div className="text-4xl font-black text-white">{fmtINR(data.financials.active_payout_pool)}</div>
                  </div>
                  <div className="pt-8 border-t border-white/5">
                      <div className="text-[10px] text-green-500 uppercase font-black tracking-widest mb-2">Operating Margin</div>
                      <div className="text-5xl font-black text-green-400">{data.financials.operating_margin_pct}%</div>
                      <div className="text-xs text-gray-500 mt-2 font-medium tracking-wide font-mono uppercase">{fmtINR(data.financials.net_surplus)} net surplus</div>
                  </div>
              </div>
          </div>

          {/* Loss Ratio per Zone */}
          <div className="col-span-12 glass-panel rounded-3xl p-8 border border-white/5">
              <h3 className="text-xs font-black uppercase text-gray-500 tracking-[0.2em] mb-8">Loss Ratio per Zone (Actual vs Premium)</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-8 gap-6">
                  {data.loss_ratios.map(z => (
                      <div key={z.zone} className="space-y-4">
                          <div className="min-h-[40px]">
                              <div className="text-[11px] font-bold text-white mb-1 line-clamp-1">{z.zone}</div>
                              <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest leading-none">{z.ratio}% ratio</div>
                          </div>
                          <div className="h-40 w-full bg-white/5 rounded-2xl relative overflow-hidden flex flex-col justify-end">
                              <div 
                                className={`w-full transition-all duration-1000 ${z.ratio > 60 ? 'bg-red-500/40' : z.ratio > 40 ? 'bg-orange-500/40' : 'bg-[#00ffcc]/40'}`} 
                                style={{ height: `${Math.min(100, z.ratio)}%` }}
                              ></div>
                          </div>
                      </div>
                  ))}
              </div>
          </div>
      </div>
    </div>
  );
}
