import React, { useState, useEffect } from 'react';

const API_BASE = 'http://localhost:8000/api';

export default function DemoController() {
  const [log, setLog] = useState([]);
  const [realWorkers, setRealWorkers] = useState([]);

  useEffect(() => {
    fetch(`${API_BASE}/admin/onboardings`)
      .then(r => r.json())
      .then(d => {
        if (d.workers && d.workers.length > 0) setRealWorkers(d.workers);
      })
      .catch(() => {});
  }, []);

  const addLog = (text, type = 'info') => {
    setLog(prev => [{
      time: new Date().toLocaleTimeString(),
      text,
      type
    }, ...prev]);
  };

  // =========================
  // MAIN SCENARIO TRIGGER
  // =========================
  const executeTrigger = async (scenario) => {
    const worker = realWorkers.length > 0
      ? realWorkers[Math.floor(Math.random() * realWorkers.length)]
      : { id: 'W-99812', name: 'Demo Worker', peb: '₹4200' };

    addLog(`🚀 Running ${scenario.toUpperCase()} scenario for ${worker.name}`, 'info');

    try {
      // ONLY trigger zone (REMOVE payout API ❌)
      const zoneRes = await fetch(`${API_BASE}/demo/trigger`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario, zone_id: 'Koramangala' })
      });

      const zoneData = await zoneRes.json();

      addLog(`🌍 SafarScore: ${zoneData.new_state.score} (${zoneData.new_state.level})`, 'score');

      // Simulate backend auto payout
      if (scenario === 'rain' || scenario === 'flood') {
        addLog(`💰 AUTO PAYOUT TRIGGERED (Backend Engine)`, 'success');
      }

      if (scenario === 'spoofer') {
        addLog(`🚫 FRAUD DETECTED - Claim Blocked`, 'error');
      }

    } catch (e) {
      addLog(`❌ Error: ${e.message}`, 'error');
    }
  };

  // =========================
  // FRAUD DEMO (REAL ENGINE)
  // =========================
  const runFraudTest = async () => {
    addLog(`🚨 Simulating Fraud Worker (Fake GPS)...`, 'error');

    try {
      const res = await fetch(`${API_BASE}/demo/fraud`, {
        method: 'POST'
      });

      const data = await res.json();

      addLog(`🧠 BPS Score: ${data.bps_score}/100`, 'score');
      addLog(`🚫 Decision: ${data.decision?.tier}`, 'error');
      addLog(`📌 Reason: ${data.reason}`, 'trace');

    } catch (e) {
      addLog(`❌ Fraud API failed: ${e.message}`, 'error');
    }
  };

  return (
    <div className="animate-fade-in px-4 max-w-4xl mx-auto">

      <h2 className="text-3xl font-bold text-[#b388ff] mb-6">
        🎮 Demo Controller
      </h2>

      {/* ================= BUTTONS ================= */}
      <div className="grid grid-cols-2 gap-6 mb-8">

        <button onClick={() => executeTrigger('rain')} className="bg-blue-900 p-6 rounded">
          🌧 Rain Event
        </button>

        <button onClick={() => executeTrigger('flood')} className="bg-red-900 p-6 rounded">
          🌊 Flood Event
        </button>

        <button onClick={() => executeTrigger('spoofer')} className="bg-yellow-900 p-6 rounded">
          🚫 Spoofer Attack
        </button>

        <button onClick={() => executeTrigger('normal')} className="bg-green-900 p-6 rounded">
          ✅ Normal
        </button>

      </div>

      {/* 🔥 FRAUD BUTTON */}
      <div className="mb-6">
        <button
          onClick={runFraudTest}
          className="bg-red-600 px-6 py-3 rounded text-white font-bold"
        >
          🚨 Simulate Fraud Detection
        </button>
      </div>

      {/* ================= LOG PANEL ================= */}
      <div className="bg-black p-4 rounded h-80 overflow-y-auto text-sm font-mono">
        {log.length === 0 ? (
          <div className="text-gray-500 text-center mt-10">
            Waiting for actions...
          </div>
        ) : (
          log.map((entry, i) => (
            <div key={i} className="mb-2">
              <span className="text-gray-600">[{entry.time}] </span>
              <span className={
                entry.type === 'error' ? 'text-red-500' :
                entry.type === 'success' ? 'text-green-400' :
                entry.type === 'score' ? 'text-blue-400' :
                entry.type === 'trace' ? 'text-gray-500' :
                'text-white'
              }>
                {entry.text}
              </span>
            </div>
          ))
        )}
      </div>

    </div>
  );
}