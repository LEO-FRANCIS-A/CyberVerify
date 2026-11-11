import React from 'react';
import { ShieldAlert } from 'lucide-react';

export default function Footer({ setActivePage }) {
  return (
    <footer className="bg-white border-t border-slate-200 mt-auto py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <div className="w-6 h-6 rounded-md bg-slate-900 flex items-center justify-center text-white">
            <ShieldAlert size={14} className="text-blue-300" />
          </div>
          <span className="font-semibold text-slate-800">CyberVerify</span>
          <span>• AI-Powered Cybersecurity Incident Intelligence Platform</span>
        </div>

        <div className="flex items-center gap-6 text-xs font-medium text-slate-600">
          <button
            onClick={() => setActivePage('dashboard')}
            className="hover:text-blue-600 transition-colors cursor-pointer"
          >
            Dashboard
          </button>
          <button
            onClick={() => setActivePage('new')}
            className="hover:text-blue-600 transition-colors cursor-pointer"
          >
            Investigate
          </button>
          <button
            onClick={() => setActivePage('history')}
            className="hover:text-blue-600 transition-colors cursor-pointer"
          >
            History
          </button>
          <button
            onClick={() => setActivePage('about')}
            className="hover:text-blue-600 transition-colors cursor-pointer"
          >
            Methodology
          </button>
        </div>

        <div className="text-[11px] text-slate-400">
          Built with FastAPI, React, MongoDB & SciPy
        </div>
      </div>
    </footer>
  );
}
