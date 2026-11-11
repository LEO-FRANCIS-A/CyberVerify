import React, { useState, useEffect } from 'react';
import { ShieldAlert, PlusCircle, LayoutDashboard, History, Info, Activity, Radio } from 'lucide-react';
import { fetchHealth } from '../services/api';

export default function Navbar({ activePage, setActivePage, onStartNew }) {
  const [isHealthy, setIsHealthy] = useState(null);

  useEffect(() => {
    fetchHealth()
      .then((data) => setIsHealthy(data.status === 'healthy'))
      .catch(() => setIsHealthy(false));

    const interval = setInterval(() => {
      fetchHealth()
        .then((data) => setIsHealthy(data.status === 'healthy'))
        .catch(() => setIsHealthy(false));
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'events', label: 'Live Events', icon: Radio },
    { id: 'new', label: 'Investigate', icon: PlusCircle },
    { id: 'history', label: 'History', icon: History },
    { id: 'about', label: 'Methodology', icon: Info },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div
          onClick={() => setActivePage('dashboard')}
          className="flex items-center gap-3 cursor-pointer group"
        >
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-slate-900 via-blue-900 to-indigo-700 flex items-center justify-center text-white shadow-md group-hover:scale-105 transition-transform">
            <ShieldAlert size={22} className="text-blue-200" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-lg font-bold tracking-tight text-slate-900">
                Cyber<span className="text-blue-600">Verify</span>
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded-sm bg-blue-50 text-blue-700 border border-blue-200">
                Dual Engine
              </span>
            </div>
            <p className="text-[11px] text-slate-500 font-medium">Verification & Event Intelligence</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map((link) => {
            const Icon = link.icon;
            const isActive = activePage === link.id;
            return (
              <button
                key={link.id}
                onClick={() => setActivePage(link.id)}
                className={`flex items-center gap-2 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-slate-100 text-blue-700 font-semibold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
                }`}
              >
                <Icon size={16} className={isActive ? 'text-blue-600' : 'text-slate-400'} />
                {link.label}
              </button>
            );
          })}
        </nav>

        {/* Right Action & System Status */}
        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-50 border border-slate-200 text-xs text-slate-600">
            <span
              className={`w-2 h-2 rounded-full ${
                isHealthy === true
                  ? 'bg-emerald-500 ring-2 ring-emerald-200 animate-pulse'
                  : isHealthy === false
                  ? 'bg-rose-500'
                  : 'bg-amber-400'
              }`}
            />
            <span className="font-medium text-[11px]">
              {isHealthy === true ? 'Dual Engine Active' : isHealthy === false ? 'Offline' : 'Connecting'}
            </span>
          </div>

          <button
            onClick={() => {
              setActivePage('new');
              if (onStartNew) onStartNew();
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium shadow-xs hover:shadow-md transition-all active:scale-95"
          >
            <PlusCircle size={16} />
            <span>Verify Claim</span>
          </button>
        </div>
      </div>
    </header>
  );
}
