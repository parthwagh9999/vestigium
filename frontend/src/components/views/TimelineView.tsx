import type { Node } from '@xyflow/react';
import { Clock, ShieldAlert, Zap, Plus, ArrowRight } from 'lucide-react';

interface TimelineViewProps {
  nodes: Node[];
  onSelectNode: (node: Node) => void;
}

export default function TimelineView({ nodes, onSelectNode }: TimelineViewProps) {
  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-y-auto p-6 select-none">
      <div className="max-w-3xl mx-auto w-full space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-400" /> Chronological Investigation Timeline
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">Discovered entities and transform history ordered chronologically.</p>
          </div>
          <span className="badge bg-blue-500/10 text-blue-400">{nodes.length} Events</span>
        </div>

        {nodes.length === 0 ? (
          <div className="text-center py-12 text-xs text-slate-500 italic">No timeline events recorded yet.</div>
        ) : (
          <div className="relative pl-6 border-l-2 border-slate-800 space-y-6">
            {nodes.map((node, idx) => {
              const label = String(node.data?.label || node.data?.value || node.id);
              const type = String(node.data?.entityType || 'custom').toUpperCase();
              const color = (node.data?.color as string) || '#3b82f6';
              const source = String(node.data?.source || 'Target Initializer');

              return (
                <div key={node.id} className="relative group cursor-pointer" onClick={() => onSelectNode(node)}>
                  {/* Timeline Dot */}
                  <div
                    className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full border-2 border-slate-950 transition-transform group-hover:scale-125"
                    style={{ background: color }}
                  />

                  <div className="p-3 rounded bg-slate-900 border border-slate-800 group-hover:border-blue-500/50 transition-all">
                    <div className="flex items-center justify-between mb-1">
                      <span className="badge" style={{ background: `${color}20`, color }}>
                        {type}
                      </span>
                      <span className="text-[10px] text-slate-500 font-mono">Event #{idx + 1}</span>
                    </div>

                    <h4 className="text-xs font-mono font-bold text-white group-hover:text-blue-300 mb-1">{label}</h4>

                    <div className="flex items-center gap-2 text-[11px] text-slate-400">
                      <Zap className="w-3 h-3 text-amber-400 shrink-0" />
                      <span>Origin: {source}</span>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
