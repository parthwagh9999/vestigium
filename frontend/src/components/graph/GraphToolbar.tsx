import React from 'react';
import { useReactFlow, Panel } from '@xyflow/react';
import { Layout, Maximize2, RefreshCw, Eye, Zap, Layers, Share2, Search, Filter, Trash2, ShieldAlert } from 'lucide-react';
import { useGraphStore, LayoutMode } from '@/stores/graphStore';
import { useParams } from 'react-router-dom';
import apiClient from '@/api/client';

export default function GraphToolbar() {
  const { fitView } = useReactFlow();
  const { 
    layoutMode, setLayoutMode, 
    animationEnabled, setAnimationEnabled,
    clusterThreshold, setClusterThreshold,
    selectedNodeIds
  } = useGraphStore();
  const { id } = useParams<{ id: string }>();
  const { setNodes, setEdges } = useReactFlow();

  const handleDeleteSelected = async () => {
    if (selectedNodeIds.size === 0 || !id) return;
    if (confirm(`Are you sure you want to delete ${selectedNodeIds.size} selected nodes?`)) {
      try {
        await apiClient.delete(`/investigations/${id}/nodes`, { data: { node_ids: Array.from(selectedNodeIds) } });
        setNodes((nds) => nds.filter((n) => !selectedNodeIds.has(n.id)));
        setEdges((eds) => eds.filter((e) => !selectedNodeIds.has(e.source) && !selectedNodeIds.has(e.target)));
      } catch (err) {
        console.error('Failed to delete nodes:', err);
      }
    }
  };

  const handleClearGraph = async () => {
    if (!id) return;
    if (confirm('Are you sure you want to clear the entire graph? This cannot be undone.')) {
      try {
        await apiClient.delete(`/investigations/${id}/clear`);
        setNodes([]);
        setEdges([]);
      } catch (err) {
        console.error('Failed to clear graph:', err);
      }
    }
  };

  return (
    <Panel position="top-left" className="mt-2 ml-2 bg-slate-900/90 backdrop-blur border border-slate-700/80 rounded-lg p-1.5 flex items-center gap-2 shadow-2xl pointer-events-auto">
      
      {/* Layout Selector */}
      <div className="flex items-center gap-1.5 px-2 border-r border-slate-700/80">
        <Layout className="w-4 h-4 text-slate-400" />
        <select 
          className="bg-transparent text-sm font-medium text-slate-200 outline-none cursor-pointer hover:text-white"
          value={layoutMode}
          onChange={(e) => setLayoutMode(e.target.value as LayoutMode)}
        >
          <option value="smart_force" className="bg-slate-800 text-slate-200">Smart Force Layout</option>
          <option value="circular_layered" className="bg-slate-800 text-slate-200">Circular Layered Layout</option>
          <option value="clustered_circular" className="bg-slate-800 text-slate-200">Clustered Circular Layout</option>
          <option value="galaxy_cluster" className="bg-slate-800 text-slate-200">Galaxy Cluster Layout</option>
          <option value="intelligence_concept" className="bg-slate-800 text-slate-200">Intelligence Concept Map</option>
        </select>
      </div>

      {/* Toggles & Sliders */}
      <div className="flex items-center gap-2 px-2 border-r border-slate-700/80">
        <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer hover:text-white" title="Enable Layout Animations">
          <Zap className={`w-3.5 h-3.5 ${animationEnabled ? 'text-amber-400' : 'text-slate-500'}`} />
          <input 
            type="checkbox" 
            checked={animationEnabled} 
            onChange={(e) => setAnimationEnabled(e.target.checked)} 
            className="hidden"
          />
          Animate
        </label>

        {layoutMode === 'clustered_circular' && (
          <label className="flex items-center gap-1.5 text-xs text-slate-300 ml-2" title="Cluster Threshold">
            <Layers className="w-3.5 h-3.5" />
            <span className="opacity-70">Cluster &gt;</span>
            <input 
              type="number" 
              value={clusterThreshold}
              onChange={(e) => setClusterThreshold(Math.max(1, parseInt(e.target.value) || 5))}
              className="w-12 bg-slate-800 border border-slate-600 rounded px-1 text-center outline-none focus:border-blue-500"
              min="1" max="100"
            />
          </label>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1">
        <button 
          onClick={handleDeleteSelected}
          disabled={selectedNodeIds.size === 0}
          className={`p-1.5 rounded transition-colors ${selectedNodeIds.size > 0 ? 'text-red-400 hover:text-white hover:bg-red-500/20' : 'text-slate-600 cursor-not-allowed'}`}
          title="Delete Selected"
        >
          <Trash2 className="w-4 h-4" />
        </button>
        <button 
          onClick={handleClearGraph}
          className="p-1.5 rounded text-orange-400 hover:text-white hover:bg-orange-500/20 transition-colors"
          title="Clear Graph"
        >
          <ShieldAlert className="w-4 h-4" />
        </button>
        <button onClick={() => fitView({ padding: 0.2, duration: 800 })} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Fit to Screen">
          <Maximize2 className="w-4 h-4" />
        </button>
        <button onClick={() => fitView({ padding: 0.2 })} className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Center Graph">
          <Eye className="w-4 h-4" />
        </button>
        <button className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Reset Layout">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>
      
      <div className="w-px h-5 bg-slate-700/80 mx-1" />
      
      <div className="flex items-center gap-1 px-1">
        <button className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Search Entities">
          <Search className="w-4 h-4" />
        </button>
        <button className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Filter Entities">
          <Filter className="w-4 h-4" />
        </button>
        <button className="p-1.5 hover:bg-slate-800 rounded text-slate-400 hover:text-white transition-colors" title="Export Graph">
          <Share2 className="w-4 h-4" />
        </button>
      </div>

    </Panel>
  );
}
