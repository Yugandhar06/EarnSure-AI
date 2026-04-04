import React, { useState, useEffect } from 'react';

export default function FraudAlerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/admin/fraud_feed');
      const data = await res.json();
      setAlerts(data.alerts || []);
      setLoading(false);
    } catch (e) {
      console.error("Fraud fetch failed", e);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
    const iv = setInterval(fetchAlerts, 5000);
    return () => clearInterval(iv);
  }, []);

  const handleAction = (id, action) => {
      alert(`${action} executed for alert ${id}`);
  };

  return (
    <div className="space-y-6 animate-fade-in pb-10 max-w-5xl mx-auto">
      
      {/* Header */}
      <header className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-wide">TrustMesh™ Network Operations</h2>
          <p className="text-gray-400 mt-1 text-sm">Real-time anomaly interception & syndicate suppression</p>
        </div>
        <div className="flex gap-4">
            <div className="px-4 py-2 bg-red-500/10 border border-red-500/20 rounded-xl text-red-500 text-xs font-black uppercase tracking-widest animate-pulse">
                Live Monitoring
            </div>
        </div>
      </header>

      {/* Grid for Active Incidents */}
      <div className="space-y-4">
          {loading ? (
              <div className="py-20 text-center text-gray-700 font-mono tracking-widest animate-pulse">SCANNING NETWORK FOR ANOMALIES...</div>
          ) : alerts.length === 0 ? (
              <div className="py-20 text-center text-gray-500 font-mono tracking-widest uppercase italic">Network clean. No active flags.</div>
          ) : alerts.map((f, i) => {
              const isRing = f.title.toLowerCase().includes('ring');
              return (
                <div key={i} className={`glass-panel rounded-3xl p-6 border transition-all ${isRing ? 'border-red-500/30 shadow-[0_0_30px_rgba(239,68,68,0.1)]' : 'border-white/5 hover:border-white/10'}`}>
                    <div className="flex items-start justify-between">
                        <div className="flex gap-4">
                            <div className="pt-1">
                                <div className={`w-3 h-3 rounded-full ${isRing ? 'bg-red-500 animate-ping' : 'bg-orange-500'}`}></div>
                            </div>
                            <div>
                                <div className="flex items-center gap-3 mb-2">
                                    <h3 className="text-lg font-black text-white">{f.title}</h3>
                                    <span className="text-[10px] text-gray-500 font-mono uppercase tracking-widest">{f.meta}</span>
                                </div>
                                <p className="text-sm text-gray-400 leading-relaxed max-w-2xl">{f.detail}</p>
                                
                                {isRing && (
                                    <div className="grid grid-cols-3 gap-6 mt-6 pb-4">
                                        <div className="space-y-1">
                                            <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest">Activations</div>
                                            <div className="text-xl font-black text-white">210</div>
                                        </div>
                                        <div className="space-y-1">
                                            <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest">New to Zone</div>
                                            <div className="text-xl font-black text-white">64%</div>
                                        </div>
                                        <div className="space-y-1">
                                            <div className="text-[10px] text-gray-500 uppercase font-black tracking-widest">Hold Status</div>
                                            <div className="text-xl font-black text-red-500">2-HR ACTIVE</div>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        <div className="flex flex-col gap-2">
                            {isRing ? (
                                <>
                                    <button onClick={() => handleAction(i, 'Release Hold')} className="px-6 py-2.5 bg-white text-black text-xs font-black uppercase tracking-widest rounded-xl hover:bg-gray-200 transition-all">Release Hold Early</button>
                                    <button onClick={() => handleAction(i, 'Restrict Zone')} className="px-6 py-2.5 border border-red-500/50 text-red-500 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-red-500/10 transition-all">Restrict Zone</button>
                                </>
                            ) : (
                                <>
                                    <button onClick={() => handleAction(i, 'Approve')} className="px-6 py-2.5 border border-white/10 text-white text-xs font-black uppercase tracking-widest rounded-xl hover:bg-white/5 transition-all">Approve Claim</button>
                                    <button onClick={() => handleAction(i, 'Ban')} className="px-6 py-2.5 border border-red-900 text-red-900 text-xs font-black uppercase tracking-widest rounded-xl hover:bg-red-900/10 transition-all">Permanent Ban</button>
                                </>
                            )}
                        </div>
                    </div>
                </div>
              );
          })}
      </div>

      {/* Network Stats Overlay */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-10">
          <div className="glass-panel p-6 rounded-2xl border border-white/5">
              <h4 className="text-[10px] text-gray-500 font-black uppercase tracking-widest mb-4">Interception Logic</h4>
              <div className="space-y-3 font-mono text-[11px]">
                  <div className="flex justify-between">
                      <span className="text-gray-500">Hard Block</span>
                      <span className="text-white">BPS &lt; 25</span>
                  </div>
                  <div className="flex justify-between">
                      <span className="text-gray-500">Manual Review</span>
                      <span className="text-white">BPS 25–49</span>
                  </div>
                  <div className="flex justify-between">
                      <span className="text-gray-500">Trust Pass</span>
                      <span className="text-[#00ffcc]">BPS &gt; 50</span>
                  </div>
              </div>
          </div>
          
          <div className="p-6 rounded-2xl border border-dashed border-white/10 flex items-center justify-center">
              <div className="text-center">
                  <div className="text-4xl mb-2">🧊</div>
                  <div className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Network Cooling Active</div>
              </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl border border-white/5 flex flex-col justify-center">
               <div className="text-4xl font-black text-white mb-1">08</div>
               <div className="text-[10px] text-gray-500 font-black uppercase tracking-widest">Attempts suppressed today</div>
          </div>
      </div>
    </div>
  );
}
