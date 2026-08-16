import React from 'react';
import { useGraphStore } from '@/stores/graphStore';
import { Eye, EyeOff, Filter, X } from 'lucide-react';

interface FilterPanelProps {
  onClose: () => void;
  entityTypes: string[];
}

export default function FilterPanel({ onClose, entityTypes }: FilterPanelProps) {
  const { hiddenEntityTypes, toggleEntityTypeVisibility, showAllEntityTypes, hideAllEntityTypes } = useGraphStore();

  return (
    <div className="absolute top-16 right-4 w-72 glass shadow-2xl rounded-xl border flex flex-col z-40 animate-slide-up"
         style={{ borderColor: 'var(--color-vestigium-border)', backdropFilter: 'blur(16px)' }}>
      <div className="flex items-center justify-between p-3 border-b" style={{ borderColor: 'var(--color-vestigium-border)' }}>
        <div className="flex items-center gap-2 text-slate-200">
          <Filter className="w-4 h-4 text-indigo-400" />
          <span className="text-sm font-semibold">Entity Visibility</span>
        </div>
        <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors">
          <X className="w-4 h-4" />
        </button>
      </div>
      
      <div className="p-3 border-b flex justify-between gap-2" style={{ borderColor: 'var(--color-vestigium-border)' }}>
        <button onClick={showAllEntityTypes} className="flex-1 btn btn-ghost text-xs py-1 text-emerald-400 hover:bg-emerald-500/10">
          <Eye className="w-3.5 h-3.5 mr-1" /> Show All
        </button>
        <button onClick={() => hideAllEntityTypes(entityTypes)} className="flex-1 btn btn-ghost text-xs py-1 text-slate-400 hover:bg-slate-800">
          <EyeOff className="w-3.5 h-3.5 mr-1" /> Hide All
        </button>
      </div>

      <div className="p-2 max-h-96 overflow-y-auto custom-scrollbar flex flex-col gap-1">
        {entityTypes.map(type => {
          const isHidden = hiddenEntityTypes.has(type);
          const prettyType = type.replace(/_/g, ' ').toUpperCase();
          
          return (
            <button
              key={type}
              onClick={() => toggleEntityTypeVisibility(type)}
              className={`flex items-center justify-between px-3 py-2 rounded-lg text-xs transition-colors ${
                isHidden ? 'text-slate-500 hover:bg-slate-800/50' : 'text-slate-200 hover:bg-slate-800'
              }`}
            >
              <span className="font-semibold tracking-wider">{prettyType}</span>
              {isHidden ? (
                <EyeOff className="w-3.5 h-3.5" />
              ) : (
                <Eye className="w-3.5 h-3.5 text-indigo-400" />
              )}
            </button>
          );
        })}
        {entityTypes.length === 0 && (
          <div className="p-4 text-center text-xs text-slate-500 italic">No entities in graph.</div>
        )}
      </div>
    </div>
  );
}
