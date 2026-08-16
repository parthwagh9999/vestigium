import { Link, useLocation } from 'react-router-dom';
import {
  Shield,
  Network,
  Wrench,
  ShieldAlert,
  Database,
  Activity,
  Settings,
} from 'lucide-react';
import logoUrl from '@/assets/logo.png';

export default function GlobalNavigation() {
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Activity },
    { path: '/investigation/default', label: 'Investigation Workspace', icon: Network },
    { path: '/tools', label: 'Tool Center', icon: Wrench },
    { path: '/vulnerabilities', label: 'Vulnerability Center', icon: ShieldAlert },
    { path: '/evidence', label: 'Evidence & Jobs', icon: Database },
  ];

  return (
    <div className="w-14 bg-slate-950/40 backdrop-blur-xl border-r border-slate-800/50 flex flex-col items-center justify-between py-3 shrink-0 z-50 shadow-[4px_0_24px_rgba(0,0,0,0.5)]">
      <div className="flex flex-col items-center gap-4 w-full">
        <Link to="/" className="w-8 h-8 rounded flex items-center justify-center shrink-0 hover:scale-105 transition-transform mb-2" title="VESTIGIUM">
          <img src={logoUrl} alt="VESTIGIUM Logo" className="w-full h-full object-contain" />
        </Link>
        
        <div className="w-8 h-px bg-slate-800 mb-2" />

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
          
          return (
            <div key={item.path} className="relative group">
              <Link
                to={item.path}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 relative ${
                  isActive
                    ? 'bg-blue-500/20 text-blue-400 shadow-[inset_0_0_12px_rgba(59,130,246,0.3)] border border-blue-500/50'
                    : 'text-slate-400 hover:text-blue-300 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-5 h-5 transition-all duration-300 ${isActive ? 'drop-shadow-[0_0_8px_rgba(59,130,246,0.8)] scale-110' : 'group-hover:scale-110 group-hover:drop-shadow-[0_0_8px_rgba(59,130,246,0.4)]'}`} />
                {isActive && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-blue-500 rounded-r shadow-[0_0_10px_#3b82f6]" />
                )}
              </Link>
              {/* Custom Tooltip */}
              <div className="absolute left-full top-1/2 -translate-y-1/2 ml-3 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded border border-slate-700 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
                {item.label}
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex flex-col items-center gap-2 relative group">
        <button className="w-10 h-10 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/60 flex items-center justify-center transition-all duration-300">
          <Settings className="w-5 h-5 group-hover:rotate-90 group-hover:text-blue-400 transition-all duration-500" />
        </button>
        <div className="absolute left-full top-1/2 -translate-y-1/2 ml-3 px-2 py-1 bg-slate-800 text-slate-200 text-xs rounded border border-slate-700 shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all whitespace-nowrap z-50">
          Settings
        </div>
      </div>
    </div>
  );
}
