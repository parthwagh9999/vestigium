import { useState, useRef, useEffect } from 'react';
import { useConsoleStore } from '@/stores/consoleStore';
import {
  Terminal,
  Activity,
  Cpu,
  Code2,
  X,
  CheckCircle,
  AlertTriangle,
  Clock,
  Trash2,
  Loader2,
} from 'lucide-react';

interface BottomPanelProps {
  isOpen: boolean;
  onClose: () => void;
  selectedEntityRawData?: any;
}

export default function BottomPanel({ isOpen, onClose, selectedEntityRawData }: BottomPanelProps) {
  const [activeTab, setActiveTab] = useState<'logs' | 'queue' | 'api' | 'raw'>('logs');

  const { logs, queue, apiLogs, clearLogs, clearQueue, clearApiLogs } = useConsoleStore();
  const logsEndRef = useRef<HTMLDivElement>(null);
  const queueEndRef = useRef<HTMLDivElement>(null);
  const apiEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (activeTab === 'logs' && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, activeTab]);

  if (!isOpen) return null;

  return (
    <div className="h-56 bg-slate-950 border-t border-slate-800 flex flex-col z-30 shrink-0 select-none shadow-2xl">
      {/* Header Tabs Bar */}
      <div className="h-9 bg-slate-900/90 border-b border-slate-800 flex items-center justify-between px-3 text-xs backdrop-blur-md">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setActiveTab('logs')}
            className={`px-3 py-1.5 font-medium transition-colors border-b-2 ${
              activeTab === 'logs' ? 'border-blue-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Terminal className="w-3.5 h-3.5 text-blue-400" />
              <span>Console Logs</span>
              {logs.length > 0 && (
                <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded-full font-mono">
                  {logs.length}
                </span>
              )}
            </div>
          </button>

          <button
            onClick={() => setActiveTab('queue')}
            className={`px-3 py-1.5 font-medium transition-colors border-b-2 ${
              activeTab === 'queue' ? 'border-blue-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Cpu className="w-3.5 h-3.5 text-emerald-400" />
              <span>Transform Queue</span>
              {queue.length > 0 && (
                <span className="text-[10px] bg-emerald-500/20 text-emerald-300 px-1.5 py-0.2 rounded-full font-mono">
                  {queue.length}
                </span>
              )}
            </div>
          </button>

          <button
            onClick={() => setActiveTab('api')}
            className={`px-3 py-1.5 font-medium transition-colors border-b-2 ${
              activeTab === 'api' ? 'border-blue-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" />
              <span>API Responses</span>
              {apiLogs.length > 0 && (
                <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.2 rounded-full font-mono">
                  {apiLogs.length}
                </span>
              )}
            </div>
          </button>

          <button
            onClick={() => setActiveTab('raw')}
            className={`px-3 py-1.5 font-medium transition-colors border-b-2 ${
              activeTab === 'raw' ? 'border-blue-500 text-white' : 'border-transparent text-slate-400 hover:text-slate-200'
            }`}
          >
            <div className="flex items-center gap-1.5">
              <Code2 className="w-3.5 h-3.5 text-purple-400" />
              <span>Raw JSON Inspector</span>
            </div>
          </button>
        </div>

        <div className="flex items-center gap-2">
          {activeTab === 'logs' && logs.length > 0 && (
            <button onClick={clearLogs} className="text-slate-500 hover:text-white px-2 py-0.5 flex items-center gap-1 bg-slate-800/60 rounded text-[11px]">
              <Trash2 className="w-3 h-3" /> Clear Logs
            </button>
          )}
          {activeTab === 'queue' && queue.length > 0 && (
            <button onClick={clearQueue} className="text-slate-500 hover:text-white px-2 py-0.5 flex items-center gap-1 bg-slate-800/60 rounded text-[11px]">
              <Trash2 className="w-3 h-3" /> Clear Queue
            </button>
          )}
          {activeTab === 'api' && apiLogs.length > 0 && (
            <button onClick={clearApiLogs} className="text-slate-500 hover:text-white px-2 py-0.5 flex items-center gap-1 bg-slate-800/60 rounded text-[11px]">
              <Trash2 className="w-3 h-3" /> Clear API Logs
            </button>
          )}
          <button onClick={onClose} className="btn btn-ghost p-1 text-slate-400 hover:text-white" title="Close Panel">
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Panel Content */}
      <div className="flex-1 overflow-y-auto p-3 font-mono text-xs text-slate-300 custom-scrollbar">
        {/* Console Logs Tab */}
        {activeTab === 'logs' && (
          <div className="space-y-1.5">
            {logs.length === 0 ? (
              <div className="text-slate-500 italic py-6 text-center">
                No logs recorded for this investigation. Run a transform or start auto-investigation.
              </div>
            ) : (
              logs.map((log, idx) => (
                <div key={idx} className="flex items-center gap-2.5 hover:bg-slate-900/50 p-1 rounded transition-colors">
                  <span className="text-slate-500 text-[10px]">{log.time}</span>
                  <span
                    className={`text-[9px] px-1.5 py-0.5 rounded uppercase font-bold tracking-wider ${
                      log.level === 'SUCCESS'
                        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                        : log.level === 'ERROR'
                        ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                        : log.level === 'WARNING'
                        ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        : 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                    }`}
                  >
                    {log.level}
                  </span>
                  <span className="text-slate-200">{log.message}</span>
                </div>
              ))
            )}
            <div ref={logsEndRef} />
          </div>
        )}

        {/* Transform Queue Tab */}
        {activeTab === 'queue' && (
          <div className="space-y-2">
            {queue.length === 0 ? (
              <div className="text-slate-500 italic py-6 text-center">
                No active or queued transform tasks for this investigation.
              </div>
            ) : (
              queue.map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-900/70 border border-slate-800 hover:border-slate-700 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    {item.status === 'running' ? (
                      <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />
                    ) : item.status === 'completed' ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : item.status === 'failed' ? (
                      <AlertTriangle className="w-4 h-4 text-red-400" />
                    ) : (
                      <Clock className="w-4 h-4 text-slate-500" />
                    )}

                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-white">{item.transformId}</span>
                      <span className="text-slate-400 text-xs">
                        Target: <strong className="text-blue-300 font-normal">{item.targetValue}</strong>
                      </span>
                      {item.entitiesCreated !== undefined && item.entitiesCreated > 0 && (
                        <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/30 px-1.5 py-0.5 rounded">
                          +{item.entitiesCreated} entities
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                    <span>{item.time}</span>
                    {item.durationSeconds !== undefined && (
                      <span className="text-slate-400 font-mono">({item.durationSeconds.toFixed(2)}s)</span>
                    )}
                  </div>
                </div>
              ))
            )}
            <div ref={queueEndRef} />
          </div>
        )}

        {/* API Responses Tab */}
        {activeTab === 'api' && (
          <div className="space-y-1.5">
            {apiLogs.length === 0 ? (
              <div className="text-slate-500 italic py-6 text-center">
                No API requests recorded for this investigation session.
              </div>
            ) : (
              apiLogs.map((api) => (
                <div
                  key={api.id}
                  className="flex items-center justify-between hover:bg-slate-900/60 p-1.5 rounded transition-colors text-xs"
                >
                  <div className="flex items-center gap-2.5">
                    <span
                      className={`text-[9px] px-1.5 py-0.5 rounded font-bold uppercase font-mono ${
                        api.method === 'GET'
                          ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                          : api.method === 'POST'
                          ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                          : api.method === 'DELETE'
                          ? 'bg-red-500/20 text-red-400 border border-red-500/30'
                          : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                      }`}
                    >
                      {api.method}
                    </span>
                    <span className="text-slate-300 font-mono">{api.url}</span>
                  </div>

                  <div className="flex items-center gap-3">
                    <span
                      className={`font-bold font-mono text-[11px] ${
                        api.status >= 200 && api.status < 300
                          ? 'text-emerald-400'
                          : api.status >= 400
                          ? 'text-red-400'
                          : 'text-amber-400'
                      }`}
                    >
                      {api.status} {api.statusText || ''}
                    </span>
                    <span className="text-slate-500 text-[10px]">({api.durationMs}ms)</span>
                    <span className="text-slate-600 text-[10px]">{api.time}</span>
                  </div>
                </div>
              ))
            )}
            <div ref={apiEndRef} />
          </div>
        )}

        {/* Raw JSON Inspector Tab */}
        {activeTab === 'raw' && (
          <pre className="text-slate-300 text-xs whitespace-pre-wrap leading-relaxed">
            {selectedEntityRawData
              ? JSON.stringify(selectedEntityRawData, null, 2)
              : '// Select an entity or transform result from the graph to inspect its raw JSON payload.'}
          </pre>
        )}
      </div>
    </div>
  );
}
