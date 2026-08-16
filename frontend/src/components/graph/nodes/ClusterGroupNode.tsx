import React from 'react';
import { NodeProps, Handle, Position } from '@xyflow/react';
import { Network, Minimize2, Maximize2 } from 'lucide-react';
import { useGraphStore } from '@/stores/graphStore';

export default function ClusterGroupNode({ id, data, selected }: NodeProps) {
  const { toggleCollapsedCluster } = useGraphStore();
  const isCollapsed = data.isCollapsed;
  const clusterColor = (data.color as string) || '#3b82f6';
  
  // Use physics-provided dimensions from data
  const w = isCollapsed ? 260 : (data.width as number || 400);
  const h = isCollapsed ? 100 : (data.height as number || 400);

  return (
    <div
      className={`relative transition-all duration-500 ease-in-out ${
        isCollapsed
          ? 'bg-slate-900/90 backdrop-blur-md rounded-xl border-2'
          : 'bg-slate-900/20 backdrop-blur-[2px] rounded-full border-2 border-dashed hover:bg-slate-900/30'
      } ${
        selected ? 'border-opacity-100 shadow-[0_0_30px_rgba(59,130,246,0.3)]' : 'border-opacity-40'
      }`}
      style={{
        width: w,
        height: h,
        borderColor: clusterColor,
        ...(!isCollapsed && {
           boxShadow: `inset 0 0 50px -20px ${clusterColor}40`,
        })
      }}
    >
      <Handle type="target" position={Position.Top} className="opacity-0 pointer-events-none" />
      <Handle type="source" position={Position.Bottom} className="opacity-0 pointer-events-none" />
      
      {/* Cluster Header */}
      <div 
        className={`absolute flex items-center justify-between gap-3 bg-slate-900/95 border border-slate-700 p-2 rounded-lg shadow-xl z-50 ${
          isCollapsed
            ? 'top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[90%]'
            : 'top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 min-w-[200px]'
        }`}
      >
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded bg-slate-800 flex items-center justify-center" style={{ color: clusterColor }}>
            <Network className="w-5 h-5" />
          </div>
          <div>
            <p className="text-sm font-bold text-white truncate max-w-[120px]" title={data.label as string}>{data.label as React.ReactNode}</p>
            <p className="text-xs text-slate-400 font-medium">{(data.count as number) || 0} Entities</p>
          </div>
        </div>

        <button 
          onClick={(e) => {
            e.stopPropagation();
            toggleCollapsedCluster(id);
          }}
          className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors cursor-pointer pointer-events-auto"
          title={isCollapsed ? "Expand Cluster" : "Collapse Cluster"}
        >
          {isCollapsed ? <Maximize2 className="w-4 h-4" /> : <Minimize2 className="w-4 h-4" />}
        </button>
      </div>

    </div>
  );
}
