import type { Node, Edge } from '@xyflow/react';
import { Activity, LayoutGrid, Zap, ShieldAlert, GitMerge, FileText } from 'lucide-react';

interface DashboardViewProps {
  nodes: Node[];
  edges: Edge[];
}

export default function DashboardView({ nodes, edges }: DashboardViewProps) {
  // Compute basic stats
  const totalEntities = nodes.length;
  const totalRelationships = edges.length;
  
  const entityTypes = nodes.reduce((acc, node) => {
    const type = String(node.data?.entityType || 'custom');
    acc[type] = (acc[type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sources = nodes.reduce((acc, node) => {
    const source = String(node.data?.source || 'Manual');
    acc[source] = (acc[source] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Compute confidence tiers
  let highConf = 0;
  let modConf = 0;
  let lowConf = 0;
  
  nodes.forEach(n => {
    const conf = (n.data?.confidence as number) || 1.0;
    if (conf >= 0.75) highConf++;
    else if (conf >= 0.4) modConf++;
    else lowConf++;
  });

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-y-auto p-6 select-none">
      <div className="max-w-5xl mx-auto w-full space-y-6">
        
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div>
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <LayoutGrid className="w-4 h-4 text-emerald-400" /> Investigation Dashboard
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">High-level overview and analytics for the current investigation.</p>
          </div>
        </div>

        {/* Top KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="glass-subtle p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center justify-between">
              <span className="text-xs font-semibold">Total Entities</span>
              <Activity className="w-4 h-4 text-blue-400" />
            </div>
            <div className="text-2xl font-bold text-white">{totalEntities}</div>
          </div>
          
          <div className="glass-subtle p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center justify-between">
              <span className="text-xs font-semibold">Relationships</span>
              <GitMerge className="w-4 h-4 text-purple-400" />
            </div>
            <div className="text-2xl font-bold text-white">{totalRelationships}</div>
          </div>
          
          <div className="glass-subtle p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center justify-between">
              <span className="text-xs font-semibold">High Confidence</span>
              <ShieldAlert className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-2xl font-bold text-white">{highConf}</div>
          </div>
          
          <div className="glass-subtle p-4 rounded-xl border border-slate-800">
            <div className="text-slate-400 mb-1 flex items-center justify-between">
              <span className="text-xs font-semibold">Data Sources</span>
              <Zap className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-2xl font-bold text-white">{Object.keys(sources).length}</div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Entity Type Breakdown */}
          <div className="glass p-5 rounded-xl border border-slate-800">
            <h3 className="text-sm font-semibold text-white mb-4">Entity Types</h3>
            {Object.keys(entityTypes).length === 0 ? (
              <p className="text-xs text-slate-500 italic">No entities yet.</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(entityTypes)
                  .sort((a, b) => b[1] - a[1])
                  .map(([type, count]) => (
                  <div key={type} className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 capitalize">{type.replace(/_/g, ' ')}</span>
                    <div className="flex items-center gap-3 w-1/2">
                      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 rounded-full" 
                          style={{ width: `${(count / totalEntities) * 100}%` }}
                        />
                      </div>
                      <span className="text-white font-mono">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          {/* Sources Breakdown */}
          <div className="glass p-5 rounded-xl border border-slate-800">
            <h3 className="text-sm font-semibold text-white mb-4">Intelligence Sources</h3>
            {Object.keys(sources).length === 0 ? (
              <p className="text-xs text-slate-500 italic">No sources yet.</p>
            ) : (
              <div className="space-y-3">
                {Object.entries(sources)
                  .sort((a, b) => b[1] - a[1])
                  .map(([source, count]) => (
                  <div key={source} className="flex items-center justify-between text-xs">
                    <span className="text-slate-300 truncate max-w-[150px]">{source}</span>
                    <div className="flex items-center gap-3 w-1/2">
                      <div className="flex-1 h-2 bg-slate-800 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-amber-500 rounded-full" 
                          style={{ width: `${(count / totalEntities) * 100}%` }}
                        />
                      </div>
                      <span className="text-white font-mono">{count}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
}
