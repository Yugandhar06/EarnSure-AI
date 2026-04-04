import React from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import ZoneMap from './pages/ZoneMap';
import Payouts from './pages/Payouts';
import FraudAlerts from './pages/FraudAlerts';
import PlanAnalytics from './pages/PlanAnalytics';
import Analytics from './pages/Analytics';
import DemoController from './pages/DemoController';
import Register from './pages/worker/Register';
import Login from './pages/worker/Login';
import WorkerPlanSelector from './pages/worker/PlanSelect';
import WorkerActive from './pages/worker/WorkerActive';

const AppSidebar = () => {
  const location = useLocation();
  // Hide sidebar on worker-facing pages
  const workerPages = ['/worker/register', '/worker/login', '/worker/plans', '/worker/active'];
  if (workerPages.some(p => location.pathname.startsWith('/worker'))) return null;

  const navItems = [
    { path: '/', label: 'Overview Metrics' },
    { path: '/plans', label: 'Plan Analytics' },
    { path: '/zones', label: 'Live Zone Map' },
    { path: '/payouts', label: 'Payout Log' },
    { path: '/fraud', label: 'TrustMesh & Fraud' },
    { path: '/demo', label: '🎮 Hackathon Demo Controls' },
  ];

  return (
    <div className="w-64 glass-panel border-r border-[#333] h-screen flex flex-col fixed shadow-2xl z-10">
      <div className="py-10 px-6 flex flex-col items-center gap-6 border-b border-[#333]/50 bg-white/2 overflow-hidden">
        <div className="relative group cursor-default w-full flex justify-center pb-4">
           <img src="/guidewire_premium.png" alt="Guidewire" className="h-12 w-full object-contain brightness-150 transition-all duration-500 scale-[2.5] hover:scale-[2.8]" />
           <div className="absolute inset-0 bg-blue-500/10 blur-3xl rounded-full opacity-0 group-hover:opacity-100 transition-all pointer-events-none"></div>
        </div>
        <div className="text-center">
            <h1 className="text-[#00ffcc] font-black text-2xl tracking-[0.25em] glow-text leading-none">SMARTSHIFT+</h1>
            <div className="mt-2 text-[9px] text-gray-500 font-black uppercase tracking-[0.15em] opacity-60">Impact Protection Console</div>
        </div>
      </div>
      <nav className="flex-1 px-4 py-8 space-y-2">
        {navItems.map((item) => {
          const active = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`block px-4 py-3 rounded-lg transition-all duration-300 ${active ? 'bg-[#00ffcc] text-black font-bold shadow-[0_0_15px_rgba(0,255,204,0.3)]' : 'text-gray-400 hover:bg-[#1a1a1a] hover:text-white'}`}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      {/* Worker Portal Link */}
      <div className="px-4 pb-4">
        <Link to="/worker/register" className="block px-4 py-3 rounded-lg border border-[#00ffcc]/30 text-[#00ffcc] text-sm text-center hover:bg-[#00ffcc]/10 transition-all">
          👷 Worker Portal →
        </Link>
      </div>
      <div className="p-6 border-t border-[#333]">
        <div className="flex items-center space-x-3">
          <div className="w-3 h-3 rounded-full bg-[#00ffcc] animate-pulse"></div>
          <span className="text-xs text-gray-400 uppercase tracking-widest">System Online</span>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AppLayout />
    </BrowserRouter>
  );
}

function AppLayout() {
  const location = useLocation();
  const isWorkerPage = location.pathname.startsWith('/worker');

  return (
    <div className={`flex min-h-screen bg-[#121212] font-sans`}>
      <AppSidebar />
      <main className={`flex-1 ${isWorkerPage ? '' : 'ml-64 p-10'} overflow-y-auto h-screen custom-scrollbar relative z-0`}>
        <Routes>
          {/* Admin Routes */}
          <Route path="/" element={<Analytics />} />
          <Route path="/plans" element={<PlanAnalytics />} />
          <Route path="/zones" element={<ZoneMap />} />
          <Route path="/payouts" element={<Payouts />} />
          <Route path="/fraud" element={<FraudAlerts />} />
          <Route path="/demo" element={<DemoController />} />

          {/* Worker Portal Routes */}
          <Route path="/worker/register" element={<Register />} />
          <Route path="/worker/login" element={<Login />} />
          <Route path="/worker/plans" element={<WorkerPlanSelector />} />
          <Route path="/worker/active" element={<WorkerActive />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
