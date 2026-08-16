import React, { useState } from 'react';
import { Play, ShieldAlert, X, Shield, Activity, Target } from 'lucide-react';

interface ToolParam {
  name: string;
  display_name: string;
  param_type: string;
  required: boolean;
}

interface OSINTTool {
  id: string;
  name: string;
  description: string;
  passive_or_active: string;
  is_passive: boolean;
  timeout: number;
  params: ToolParam[];
  input_entity_types: string[];
}

interface TransformRunnerModalProps {
  tool: OSINTTool;
  onClose: () => void;
  onRun: (targetValue: string, targetType: string, params: Record<string, string>) => void;
  isOpen: boolean;
}

export default function TransformRunnerModal({ tool, onClose, onRun, isOpen }: TransformRunnerModalProps) {
  const [targetValue, setTargetValue] = useState('');
  const [targetType, setTargetType] = useState(tool.input_entity_types[0] || 'domain');
  const [params, setParams] = useState<Record<string, string>>({});
  const [authorized, setAuthorized] = useState(false);

  if (!isOpen) return null;

  const isActive = tool.passive_or_active === 'ACTIVE_AUTHORIZED' || !tool.is_passive;
  const canRun = isActive ? authorized && targetValue.trim() !== '' : targetValue.trim() !== '';

  const handleRun = () => {
    if (canRun) {
      onRun(targetValue, targetType, params);
    }
  };

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
      <div className="glass rounded-2xl border border-slate-700/80 bg-slate-900/95 w-full max-w-lg flex flex-col overflow-hidden shadow-2xl shadow-blue-500/10">
        
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-start justify-between bg-slate-800/40">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${isActive ? 'bg-red-500/10 border border-red-500/30 text-red-400' : 'bg-blue-500/10 border border-blue-500/30 text-blue-400'}`}>
              {isActive ? <ShieldAlert className="w-5 h-5" /> : <Play className="w-5 h-5" />}
            </div>
            <div>
              <h2 className="text-base font-bold text-white tracking-wide">
                Run Transform
              </h2>
              <p className="text-xs text-slate-400">{tool.name}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6">
          
          {/* Target Selection */}
          <div className="space-y-3">
            <label className="text-xs font-mono uppercase tracking-wider text-slate-500 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" /> Target Entity
            </label>
            <div className="flex gap-2">
              <select
                value={targetType}
                onChange={(e) => setTargetType(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 w-1/3 outline-none focus:border-blue-500"
              >
                {tool.input_entity_types.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
              <input
                type="text"
                placeholder="Enter target value..."
                value={targetValue}
                onChange={(e) => setTargetValue(e.target.value)}
                className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-2 flex-1 outline-none focus:border-blue-500"
              />
            </div>
          </div>

          {/* Optional Params */}
          {tool.params && tool.params.length > 0 && (
            <div className="space-y-3">
              <label className="text-xs font-mono uppercase tracking-wider text-slate-500">Configuration</label>
              {tool.params.map(param => (
                <div key={param.name} className="flex items-center justify-between gap-4">
                  <span className="text-sm text-slate-300">{param.display_name}</span>
                  <input
                    type="text"
                    value={params[param.name] || ''}
                    onChange={(e) => setParams({...params, [param.name]: e.target.value})}
                    placeholder={param.required ? "Required" : "Optional"}
                    className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg px-3 py-1.5 w-1/2 outline-none focus:border-blue-500"
                  />
                </div>
              ))}
            </div>
          )}

          {/* Warning Banner for Active Tools */}
          {isActive && (
            <div className="p-4 rounded-xl bg-red-950/30 border border-red-900/50 space-y-3">
              <div className="flex gap-2 items-start text-red-400">
                <ShieldAlert className="w-5 h-5 shrink-0" />
                <div className="space-y-1">
                  <h4 className="text-sm font-bold tracking-wide uppercase">Authorized Security Assessment</h4>
                  <p className="text-xs text-red-400/80 leading-relaxed">
                    This transform generates aggressive, highly-detectable network traffic that touches the target directly.
                  </p>
                </div>
              </div>
              
              <div className="pt-2">
                <label className="flex items-center gap-3 cursor-pointer group">
                  <div className={`w-5 h-5 rounded border flex items-center justify-center transition-colors ${authorized ? 'bg-red-500 border-red-500 text-white' : 'bg-slate-900 border-slate-700 group-hover:border-slate-500 text-transparent'}`}>
                    <CheckCircle className="w-3.5 h-3.5" />
                  </div>
                  <span className="text-sm text-slate-300 select-none group-hover:text-slate-200">
                    I confirm that I am authorized to actively scan <strong className="text-white">{targetValue || "this target"}</strong>.
                  </span>
                  <input
                    type="checkbox"
                    className="hidden"
                    checked={authorized}
                    onChange={(e) => setAuthorized(e.target.checked)}
                  />
                </label>
              </div>
            </div>
          )}

          <div className="flex items-center justify-between text-xs text-slate-500 border-t border-slate-800 pt-4">
            <span className="flex items-center gap-1.5"><Activity className="w-3.5 h-3.5" /> {tool.passive_or_active.replace(/_/g, ' ')}</span>
            <span className="flex items-center gap-1.5">Timeout: {tool.timeout}s</span>
          </div>

        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
          <button
            onClick={onClose}
            className="btn btn-secondary text-xs px-4 h-9"
          >
            Cancel
          </button>
          <button
            onClick={handleRun}
            disabled={!canRun}
            className={`btn text-xs px-5 h-9 gap-2 shadow-lg transition-all ${
              isActive 
                ? canRun ? 'bg-red-600 hover:bg-red-500 text-white shadow-red-500/20' : 'bg-red-900/50 text-red-500/50 cursor-not-allowed border-none'
                : canRun ? 'btn-primary shadow-blue-500/20' : 'bg-slate-800 text-slate-500 cursor-not-allowed border-none'
            }`}
          >
            {isActive ? <Shield className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            {isActive ? 'Run Authorized Assessment' : 'Run Transform'}
          </button>
        </div>

      </div>
    </div>
  );
}

// Since CheckCircle was missing in imports, adding it at the top level
const CheckCircle = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
);
