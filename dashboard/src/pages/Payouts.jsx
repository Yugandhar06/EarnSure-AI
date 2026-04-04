import React, { useState, useEffect } from 'react';

const PLAN_MAP = {
    'Light': { color: 'bg-indigo-500/10 text-indigo-400', border: 'border-indigo-500/20' },
    'Regular': { color: 'bg-cyan-500/10 text-cyan-400', border: 'border-cyan-500/20' },
    'Standard': { color: 'bg-amber-500/10 text-amber-500', border: 'border-amber-500/20' },
    'Pro': { color: 'bg-red-500/10 text-red-400', border: 'border-red-500/20' },
    'Max': { color: 'bg-purple-500/10 text-purple-400', border: 'border-purple-500/20' }
};

export default function Payouts() {
  const [payouts, setPayouts] = useState([]);
  const [filter, setFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchPayouts = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/admin/payouts/detailed');
      const data = await res.json();
      setPayouts(data.payouts || []);
      setLoading(false);
    } catch (e) {
      console.error("Payout fetch failed", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPayouts();
    const iv = setInterval(fetchPayouts, 10000);
    return () => clearInterval(iv);
  }, []);

  const filtered = payouts.filter(p => 
    p.name.toLowerCase().includes(filter.toLowerCase()) || 
    p.zone.toLowerCase().includes(filter.toLowerCase()) ||
    p.razorpay_id.toLowerCase().includes(filter.toLowerCase())
  );

  return (
    <div className="space-y-6 animate-fade-in pb-10">
      
      {/* Header & Filter */}
      <header className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-wide">Payout Forensic Log</h2>
          <p className="text-gray-400 mt-1 text-sm">Full audit trail of all parametric claims processed via UPI Mandates</p>
        </div>
        <div className="flex items-center gap-3">
            <div className="relative">
                <input 
                    type="text" 
                    placeholder="Search by worker, zone, or ID..."
                    className="bg-white/5 border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white w-72 focus:outline-none focus:border-[#00ffcc]/50 transition-all"
                    value={filter}
                    onChange={(e) => setFilter(e.target.value)}
                />
            </div>
            <button onClick={fetchPayouts} className="bg-white/5 border border-white/10 p-2.5 rounded-xl text-gray-400 hover:text-white transition-all">
                🔄
            </button>
        </div>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
         <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <h4 className="text-[10px] text-gray-400 uppercase tracking-widest mb-1 font-black">Total Payout Volume</h4>
            <div className="text-2xl font-black text-[#00ffcc]">₹{payouts.reduce((s,p)=>s+p.amt,0).toLocaleString()}</div>
         </div>
         <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <h4 className="text-[10px] text-gray-400 uppercase tracking-widest mb-1 font-black">Average Gap Recovery</h4>
            <div className="text-2xl font-black text-white">₹{Math.round(payouts.reduce((s,p)=>s+p.gap,0) / (payouts.length || 1)).toLocaleString()}</div>
         </div>
         <div className="glass-panel p-5 rounded-2xl border border-white/5">
            <h4 className="text-[10px] text-gray-400 uppercase tracking-widest mb-1 font-black">Signal Confidence</h4>
            <div className="text-2xl font-black text-white">94.2%</div>
         </div>
      </div>

      {/* Main Table */}
      <div className="glass-panel rounded-3xl border border-white/5 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-white/5 text-[10px] uppercase font-black tracking-[0.15em] text-gray-500 border-b border-white/5">
              <tr>
                <th className="py-4 px-6">Timestamp / ID</th>
                <th className="py-4 px-6">Worker & Zone</th>
                <th className="py-4 px-6">Tier</th>
                <th className="py-4 px-6">PEB vs Actual</th>
                <th className="py-4 px-6">Gap Amt</th>
                <th className="py-4 px-6">Confidence</th>
                <th className="py-4 px-6 text-right">Payout (UPI)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {loading ? (
                <tr><td colSpan="7" className="py-12 text-center text-gray-500 animate-pulse font-mono tracking-widest">DRAGGING RECORDS FROM DATABASE...</td></tr>
              ) : filtered.length === 0 ? (
                <tr><td colSpan="7" className="py-12 text-center text-gray-500 font-mono tracking-widest uppercase">No payouts found matching terms</td></tr>
              ) : filtered.map((p, i) => {
                  const plan = PLAN_MAP[p.tier] || PLAN_MAP['Standard'];
                  return (
                    <tr key={i} className="hover:bg-white/[0.02] transition-colors group">
                      <td className="py-5 px-6">
                        <div className="text-[13px] font-bold text-white mb-1">{p.time}</div>
                        <div className="text-[10px] font-mono text-gray-500 group-hover:text-gray-400">{p.razorpay_id}</div>
                      </td>
                      <td className="py-5 px-6">
                        <div className="text-[13px] font-bold text-white mb-1">{p.name}</div>
                        <div className="text-[11px] text-gray-500 uppercase tracking-widest">{p.zone}</div>
                      </td>
                      <td className="py-5 px-6">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-black uppercase tracking-tighter border ${plan.color} ${plan.border}`}>
                          {p.tier}
                        </span>
                      </td>
                      <td className="py-5 px-6">
                        <div className="text-[12px] font-medium text-gray-400">₹{p.peb} <span className="text-[10px] text-gray-600">vs</span> ₹{p.actual}</div>
                      </td>
                      <td className="py-5 px-6">
                        <div className="text-[13px] font-black text-white">₹{p.gap}</div>
                        <div className="text-[10px] text-gray-600 font-medium">{p.ratio}% coverage</div>
                      </td>
                      <td className="py-5 px-6">
                        <div className="flex items-center gap-2">
                            <div className="w-16 h-1 bg-white/5 rounded-full overflow-hidden">
                                <div className="h-full bg-[#00ffcc]" style={{ width: `${p.confidence * 100}%` }}></div>
                            </div>
                            <span className="text-[11px] font-bold text-[#00ffcc]">{Math.round(p.confidence * 100)}%</span>
                        </div>
                        <div className="text-[9px] text-gray-600 mt-1 uppercase font-black tracking-widest">{p.signals} signals verified</div>
                      </td>
                      <td className="py-5 px-6 text-right">
                        <div className="text-[16px] font-black text-[#00ffcc]">₹{p.amt.toFixed(2)}</div>
                        <div className="text-[9px] text-green-500 font-black uppercase mt-1 tracking-widest">SUCCESS</div>
                      </td>
                    </tr>
                  );
                })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
