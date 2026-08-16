import { useState } from 'react';
import {
  Shield,
  Network,
  Table,
  Clock,
  Globe,
  Grid,
  CheckSquare,
  Search,
  Command,
  Activity,
  Terminal,
  ChevronDown,
  Layers,
  User,
  Settings,
  LogOut,
  Bell,
  Cpu,
} from 'lucide-react';
import { Link } from 'react-router-dom';

interface AppHeaderProps {
  investigationName: string;
  investigationStatus: string;
  activeView: 'graph' | 'table' | 'timeline' | 'map' | 'matrix' | 'kanban' | 'dashboard';
  onViewChange: (view: 'graph' | 'table' | 'timeline' | 'map' | 'matrix' | 'kanban' | 'dashboard') => void;
  onOpenCommandPalette: () => void;
  onOpenSearch: () => void;
  onToggleBottomPanel: () => void;
  bottomPanelOpen: boolean;
}

export default function AppHeader({
  investigationName,
  investigationStatus,
  activeView,
  onViewChange,
  onOpenCommandPalette,
  onOpenSearch,
  onToggleBottomPanel,
  bottomPanelOpen,
}: AppHeaderProps) {
  const [showWorkspaceMenu, setShowWorkspaceMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const views = [
    { id: 'dashboard', label: 'Dashboard', icon: Activity },
    { id: 'graph', label: 'Graph', icon: Network },
    { id: 'table', label: 'Table', icon: Table },
    { id: 'timeline', label: 'Timeline', icon: Clock },
    { id: 'map', label: 'Map', icon: Globe },
    { id: 'matrix', label: 'Matrix', icon: Grid },
    { id: 'kanban', label: 'Tasks', icon: CheckSquare },
  ] as const;

  return (
    <header className="h-11 bg-slate-950 border-b border-slate-800 flex items-center justify-between px-3 text-xs select-none shrink-0 z-30">
      {/* Left Branding & Workspace */}
      <div className="flex items-center gap-3">
        <Link to="/" className="flex items-center gap-2 font-bold tracking-wider text-white text-xs hover:opacity-80 transition-opacity">
          <div className="w-6 h-6 rounded bg-blue-600 border border-blue-500 flex items-center justify-center text-white shrink-0">
            <Shield className="w-3.5 h-3.5 fill-current" />
          </div>
          <span className="hidden sm:inline">VESTIGIUM <span className="text-blue-500 font-normal">INTEL</span></span>
        </Link>

        <div className="h-4 w-px bg-slate-800" />

        {/* Workspace Switcher Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowWorkspaceMenu(!showWorkspaceMenu)}
            className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-300 font-medium"
          >
            <Layers className="w-3 h-3 text-blue-400" />
            <span className="truncate max-w-[110px]">Default Workspace</span>
            <ChevronDown className="w-3 h-3 text-slate-500" />
          </button>

          {showWorkspaceMenu && (
            <div className="absolute left-0 top-full mt-1 w-48 bg-slate-900 border border-slate-800 rounded shadow-2xl p-1 z-50">
              <div className="px-2 py-1 text-[10px] font-bold text-slate-500 uppercase tracking-wider">Workspaces</div>
              <button className="w-full text-left px-2 py-1.5 rounded bg-blue-600/20 text-blue-400 font-medium flex items-center justify-between">
                <span>Default Workspace</span>
                <span className="badge bg-blue-500/20 text-blue-400">ACTIVE</span>
              </button>
              <button className="w-full text-left px-2 py-1.5 rounded hover:bg-slate-800 text-slate-300">
                Threat Intelligence Lab
              </button>
              <button className="w-full text-left px-2 py-1.5 rounded hover:bg-slate-800 text-slate-300">
                Financial Crime Ops
              </button>
            </div>
          )}
        </div>

        <div className="h-4 w-px bg-slate-800" />

        {/* Current Investigation Name & Status */}
        <div className="flex items-center gap-2">
          <span className="font-semibold text-white truncate max-w-[180px]" title={investigationName}>
            {investigationName}
          </span>
          <span className="badge bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            {investigationStatus}
          </span>
        </div>
      </div>

      {/* Center Visualization Mode Tabs */}
      <div className="flex items-center bg-slate-900 p-0.5 rounded border border-slate-800">
        {views.map((v) => {
          const Icon = v.icon;
          const active = activeView === v.id;
          return (
            <button
              key={v.id}
              onClick={() => onViewChange(v.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${
                active
                  ? 'bg-blue-600 text-white shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span>{v.label}</span>
            </button>
          );
        })}
      </div>

      {/* Right Search, Actions & Status Controls */}
      <div className="flex items-center gap-2">
        {/* Global Search Button */}
        <button
          onClick={onOpenSearch}
          className="flex items-center gap-2 px-2.5 py-1 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
          title="Global Search (Ctrl+K)"
        >
          <Search className="w-3.5 h-3.5" />
          <span className="hidden md:inline">Search...</span>
          <kbd className="hidden lg:inline text-[10px] bg-slate-800 border border-slate-700 px-1 rounded text-slate-400 font-mono">
            Ctrl+K
          </kbd>
        </button>

        {/* Command Palette Button */}
        <button
          onClick={onOpenCommandPalette}
          className="flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200"
          title="Command Palette (Ctrl+Shift+P)"
        >
          <Command className="w-3.5 h-3.5 text-blue-400" />
          <kbd className="hidden lg:inline text-[10px] bg-slate-800 border border-slate-700 px-1 rounded text-slate-400 font-mono">
            Ctrl+Shift+P
          </kbd>
        </button>

        <div className="h-4 w-px bg-slate-800" />

        {/* Bottom Console Drawer Toggle */}
        <button
          onClick={onToggleBottomPanel}
          className={`flex items-center gap-1 px-2 py-1 rounded border transition-colors ${
            bottomPanelOpen
              ? 'bg-blue-600/20 border-blue-500/50 text-blue-400'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200'
          }`}
          title="Console & Logs Drawer"
        >
          <Terminal className="w-3.5 h-3.5" />
          <span className="hidden xl:inline text-[11px]">Console</span>
        </button>

        {/* API Status */}
        <div className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded bg-slate-900/60 border border-slate-800/80 text-[11px]" title="API System Online">
          <Activity className="w-3 h-3 text-emerald-400" />
          <span className="text-slate-400">API:</span>
          <span className="text-emerald-400 font-mono font-medium">ONLINE</span>
        </div>

        {/* User Menu Dropdown */}
        <div className="relative">
          <button
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center gap-1.5 p-1 rounded hover:bg-slate-900 text-slate-300"
          >
            <div className="w-6 h-6 rounded bg-slate-800 border border-slate-700 flex items-center justify-center text-slate-300 font-bold text-[10px]">
              AD
            </div>
          </button>

          {showUserMenu && (
            <div className="absolute right-0 top-full mt-1 w-44 bg-slate-900 border border-slate-800 rounded shadow-2xl p-1 z-50">
              <div className="px-2.5 py-1.5 border-b border-slate-800">
                <p className="font-bold text-white text-xs">admin</p>
                <p className="text-[10px] text-slate-400">System Administrator</p>
              </div>
              <button className="w-full text-left px-2.5 py-1.5 rounded hover:bg-slate-800 text-slate-300 flex items-center gap-2">
                <User className="w-3.5 h-3.5" /> Account Profile
              </button>
              <button className="w-full text-left px-2.5 py-1.5 rounded hover:bg-slate-800 text-slate-300 flex items-center gap-2">
                <Settings className="w-3.5 h-3.5" /> Preferences
              </button>
              <div className="my-1 border-t border-slate-800" />
              <button className="w-full text-left px-2.5 py-1.5 rounded hover:bg-red-500/20 text-red-400 flex items-center gap-2">
                <LogOut className="w-3.5 h-3.5" /> Sign Out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
