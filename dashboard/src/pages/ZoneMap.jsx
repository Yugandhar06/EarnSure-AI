import React, { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Circle, Popup, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Risk colour palette
const riskColor = (score) => {
  if (score >= 70) return '#ff2d55';   // Extreme - red
  if (score >= 50) return '#ff9500';   // High    - orange
  if (score >= 30) return '#ffd700';   // Moderate - gold
  return '#00ffcc';                     // Low      - teal
};

const riskLabel = (score) => {
  if (score >= 70) return 'EXTREME';
  if (score >= 50) return 'HIGH RISK';
  if (score >= 30) return 'MODERATE';
  return 'LOW RISK';
};

// Fit map to all zone markers
function FitBounds({ zones }) {
  const map = useMap();
  useEffect(() => {
    const valid = zones.filter(z => z.lat != null && z.lng != null && !isNaN(z.lat) && !isNaN(z.lng));
    if (valid.length) {
      const bounds = valid.map(z => [z.lat, z.lng]);
      map.fitBounds(bounds, { padding: [40, 40] });
    }
  }, [zones]);
  return null;
}

export default function ZoneMap() {
  const [zones, setZones] = useState([]);
  const [selected, setSelected] = useState(null);
  const [lastUpdated, setLastUpdated] = useState('');

  useEffect(() => {
    const fetchZones = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/admin/zone_risk');
        const data = await res.json();
        if (data.zones) {
          setZones(data.zones);
          setLastUpdated(new Date().toLocaleTimeString('en-IN'));
        }
      } catch (e) {
        console.error('Zone fetch failed', e);
      }
    };
    fetchZones();
    const iv = setInterval(fetchZones, 15000); // Poll every 15s (SafarScore cadence)
    return () => clearInterval(iv);
  }, []);

  const extreme = zones.filter(z => z.score >= 70).length;
  const high    = zones.filter(z => z.score >= 50 && z.score < 70).length;
  const totalWorkers = zones.reduce((s, z) => s + (z.workers || 0), 0);

  return (
    <div className="animate-fade-in h-full flex flex-col" style={{ height: 'calc(100vh - 80px)' }}>
      {/* Header */}
      <header className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="text-3xl font-bold text-white tracking-wide">Live Zone Risk Map</h2>
          <p className="text-gray-400 mt-1 text-sm">SafarScore™ · 1km grid · Bangalore · Updates every 15 min</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500 font-mono mt-2">
          <div className="w-2 h-2 rounded-full bg-[#00ffcc] animate-pulse"></div>
          Last updated: {lastUpdated || '—'}
        </div>
      </header>

      {/* Stat pills */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Zones Monitored', val: zones.length, color: '#00ffcc' },
          { label: 'Extreme Risk', val: extreme, color: '#ff2d55' },
          { label: 'High Risk', val: high, color: '#ff9500' },
          { label: 'Active Workers', val: totalWorkers.toLocaleString(), color: '#b388ff' },
        ].map((s, i) => (
          <div key={i} className="glass-panel rounded-xl p-4 border border-[#333]">
            <div className="text-2xl font-bold font-mono" style={{ color: s.color }}>{s.val}</div>
            <div className="text-xs text-gray-400 mt-1 uppercase tracking-wider">{s.label}</div>
          </div>
        ))}
      </div>

      <div className="flex gap-6 flex-1 min-h-0">
        {/* Map */}
        <div className="flex-1 rounded-2xl overflow-hidden border border-[#333] shadow-2xl" style={{ minHeight: 400 }}>
          <MapContainer
            center={[12.9716, 77.5946]}
            zoom={12}
            zoomControl={true}
            style={{ height: '100%', width: '100%', background: '#0a0a0f' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://carto.com/">CARTO</a>'
              url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            />
            <FitBounds zones={zones} />
            {zones.filter(z => z.lat != null && z.lng != null).map((zone, i) => (
              <Circle
                key={i}
                center={[zone.lat, zone.lng]}
                radius={1200}
                pathOptions={{
                  color: riskColor(zone.score),
                  fillColor: riskColor(zone.score),
                  fillOpacity: zone.trigger ? 0.55 : 0.30,
                  weight: zone.trigger ? 3 : 1.5,
                }}
                eventHandlers={{ click: () => setSelected(zone) }}
              >
                <Popup className="safarmap-popup">
                  <div style={{
                    background: '#111317', color: 'white', borderRadius: 12, padding: '12px 16px',
                    fontFamily: "'Space Grotesk', sans-serif", minWidth: 200
                  }}>
                    <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 6 }}>{zone.name}</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
                      <div style={{
                        background: riskColor(zone.score), borderRadius: 6, padding: '2px 10px',
                        fontSize: 11, fontWeight: 700, color: '#000'
                      }}>{riskLabel(zone.score)}</div>
                    </div>
                    <div style={{ fontSize: 32, fontWeight: 900, color: riskColor(zone.score), marginBottom: 4 }}>{zone.score}</div>
                    <div style={{ fontSize: 11, color: '#888' }}>SafarScore (0–100)</div>
                    <hr style={{ border: 'none', borderTop: '1px solid #333', margin: '10px 0' }} />
                    <div style={{ fontSize: 12, color: '#aaa' }}>👷 Active Workers: <strong style={{ color: '#fff' }}>{zone.workers}</strong></div>
                    {zone.trigger && (
                      <div style={{ marginTop: 8, fontSize: 11, color: '#ff9500', background: '#ff950015',
                        border: '1px solid #ff950040', borderRadius: 6, padding: '4px 8px' }}>
                        ⚡ Payout Trigger Active
                      </div>
                    )}
                  </div>
                </Popup>
              </Circle>
            ))}
          </MapContainer>
        </div>

        {/* Zone List Sidebar */}
        <div className="w-72 flex flex-col gap-2 overflow-y-auto custom-scrollbar">
          <div className="text-xs text-gray-500 uppercase tracking-widest font-semibold mb-2 px-1">All Zones</div>
          {zones.sort((a, b) => b.score - a.score).map((zone, i) => (
            <div
              key={i}
              onClick={() => setSelected(zone)}
              className="glass-panel rounded-xl p-4 border cursor-pointer transition-all hover:scale-[1.02]"
              style={{
                borderColor: selected?.name === zone.name ? riskColor(zone.score) : '#222',
                boxShadow: selected?.name === zone.name ? `0 0 12px ${riskColor(zone.score)}55` : 'none'
              }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="font-semibold text-sm text-white">{zone.name}</div>
                <div className="text-xl font-black font-mono" style={{ color: riskColor(zone.score) }}>{zone.score}</div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold px-2 py-0.5 rounded-full" style={{
                  background: riskColor(zone.score) + '22',
                  color: riskColor(zone.score)
                }}>{riskLabel(zone.score)}</span>
                <span className="text-xs text-gray-500">👷 {zone.workers}</span>
              </div>
              {zone.trigger && (
                <div className="mt-2 text-xs text-orange-400 flex items-center gap-1">
                  <div className="w-1.5 h-1.5 rounded-full bg-orange-400 animate-pulse"></div>
                  Payout Trigger Active
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 mt-4 pt-4 border-t border-[#222]">
        <span className="text-xs text-gray-500 uppercase tracking-widest">Risk Scale:</span>
        {[
          { label: 'Low Risk (0–29)', color: '#00ffcc' },
          { label: 'Moderate (30–49)', color: '#ffd700' },
          { label: 'High Risk (50–69)', color: '#ff9500' },
          { label: 'Extreme (70+)', color: '#ff2d55' },
        ].map((l, i) => (
          <div key={i} className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ background: l.color }}></div>
            <span className="text-xs text-gray-400">{l.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
