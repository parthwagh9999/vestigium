import React, { useMemo } from 'react';
import { Eye, EyeOff, Layers, CheckSquare, Square } from 'lucide-react';
import { useReactFlow, Node } from '@xyflow/react';
import { useGraphStore } from '@/stores/graphStore';

export default function EntityVisibilityPanel() {
  const { getNodes } = useReactFlow();
  const nodes = getNodes();
  
  const { hiddenEntityTypes, toggleEntityTypeVisibility, showAllEntityTypes, hideAllEntityTypes } = useGraphStore();

  // Dynamically calculate unique entity types present in the graph and their counts
  const entityStats = useMemo(() => {
    const stats: Record<string, { count: number; color: string }> = {};
    nodes.forEach((n: Node) => {
      if (n.type === 'entity' && n.data?.entityType) {
        const type = n.data.entityType as string;
        if (!stats[type]) {
          stats[type] = { count: 0, color: (n.data.color as string) || '#fff' };
        }
        stats[type].count++;
      }
    });
    return Object.entries(stats).sort((a, b) => b[1].count - a[1].count);
  }, [nodes]);

  const allTypes = entityStats.map(([type]) => type);

  return (
    <div className="flex flex-col h-full bg-slate-900 border-l border-slate-800 shadow-2xl">
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/50">
        <div className="flex items-center gap-2">
          <Layers className="w-5 h-5 text-indigo-400" />
          <h2 className="font-semibold text-white">Entity Visibility</h2>
        </div>
        <div className="text-xs font-mono text-slate-400 bg-slate-800 px-2 py-1 rounded">
          {nodes.filter(n => n.type === 'entity').length} Total
        </div>
      </div>

      <div className="p-2 border-b border-slate-800 flex gap-2">
        <button 
          onClick={showAllEntityTypes}
          className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition-colors"
        >
          <Eye className="w-3.5 h-3.5" /> Show All
        </button>
        <button 
          onClick={() => hideAllEntityTypes(allTypes)}
          className="flex-1 flex items-center justify-center gap-1 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs rounded transition-colors"
        >
          <EyeOff className="w-3.5 h-3.5" /> Hide All
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-2 space-y-1 custom-scrollbar">
        {entityStats.length === 0 ? (
          <div className="text-center text-slate-500 py-8 text-sm">
            No entities in graph.
          </div>
        ) : (
          entityStats.map(([type, { count, color }]) => {
            const isHidden = hiddenEntityTypes.has(type);
            return (
              <div 
                key={type}
                onClick={() => toggleEntityTypeVisibility(type)}
                className={`flex items-center justify-between p-2 rounded cursor-pointer transition-colors ${
                  isHidden ? 'bg-slate-900/50 opacity-50 hover:opacity-80' : 'bg-slate-800 hover:bg-slate-700'
                }`}
              >
                <div className="flex items-center gap-3">
                  <div className="flex items-center justify-center text-slate-400">
                    {isHidden ? <Square className="w-4 h-4" /> : <CheckSquare className="w-4 h-4 text-indigo-400" />}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                    <span className="text-sm font-medium text-slate-200">{type}</span>
                  </div>
                </div>
                <span className="text-xs font-mono text-slate-500">{count}</span>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
