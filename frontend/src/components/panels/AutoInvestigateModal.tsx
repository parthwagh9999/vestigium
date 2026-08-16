import React, { useState, useEffect } from 'react';
import { Sparkles, X, Settings2, Play, Check, Loader2 } from 'lucide-react';
import apiClient from '@/api/client';

interface TransformItem {
  id: string;
  name: string;
  description: string;
  category: string;
}

interface AutoInvestigateModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStart: (depth: number, maxEntities: number, allowedTransforms: string[]) => void;
}

export default function AutoInvestigateModal({ isOpen, onClose, onStart }: AutoInvestigateModalProps) {
  const [depth, setDepth] = useState(10);
  const [maxEntities, setMaxEntities] = useState(500);
  const [transforms, setTransforms] = useState<TransformItem[]>([]);
  const [selectedTransforms, setSelectedTransforms] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchTransforms();
    }
  }, [isOpen]);

  const fetchTransforms = async () => {
    setLoading(true);
    try {
      const { data } = await apiClient.get('/transforms');
      setTransforms(data);
      setSelectedTransforms(new Set(data.map((t: any) => t.id)));
    } catch (err) {
      console.error('Failed to load transforms', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleTransform = (id: string) => {
    const next = new Set(selectedTransforms);
    if (next.has(id)) {
      next.delete(id);
    } else {
      next.add(id);
    }
    setSelectedTransforms(next);
  };

  const toggleAll = (select: boolean) => {
    if (select) {
      setSelectedTransforms(new Set(transforms.map(t => t.id)));
    } else {
      setSelectedTransforms(new Set());
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-[500px] max-h-[90vh] flex flex-col overflow-hidden animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-indigo-400" />
            <h2 className="font-bold text-white text-lg">Auto Investigate</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-6 overflow-y-auto custom-scrollbar">
          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm font-semibold text-slate-200">Investigation Depth</label>
              <span className="text-xs font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                Layer {depth}
              </span>
            </div>
            <input 
              type="range" 
              min="1" 
              max="10" 
              value={depth} 
              onChange={(e) => setDepth(Number(e.target.value))}
              className="w-full accent-indigo-500"
            />
            <div className="flex justify-between text-xs text-slate-500">
              <span>1</span>
              <span>Recursive Layers</span>
              <span>10</span>
            </div>
            <p className="text-xs text-slate-400 leading-relaxed mt-2">
              Determines how many recursive hops the engine will take. Higher depth reveals more context but significantly increases execution time and API limits.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between">
              <label className="text-sm font-semibold text-slate-200">Max Entities Limit</label>
              <span className="text-xs font-mono text-slate-400">
                {maxEntities}
              </span>
            </div>
            <input 
              type="range" 
              min="50" 
              max="2000" 
              step="50"
              value={maxEntities} 
              onChange={(e) => setMaxEntities(Number(e.target.value))}
              className="w-full accent-slate-500"
            />
            <p className="text-xs text-slate-400 leading-relaxed mt-2">
              Hard limit on the total number of entities to prevent runaway discovery loops.
            </p>
          </div>
          
          <div className="pt-4 border-t border-slate-800">
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm font-semibold text-slate-200">Selected Transforms</label>
              <div className="flex gap-2">
                <button onClick={() => toggleAll(true)} className="text-xs text-indigo-400 hover:text-indigo-300">Select All</button>
                <span className="text-slate-600">|</span>
                <button onClick={() => toggleAll(false)} className="text-xs text-slate-400 hover:text-slate-300">Deselect All</button>
              </div>
            </div>
            
            {loading ? (
              <div className="flex justify-center p-4">
                <Loader2 className="w-5 h-5 text-indigo-400 animate-spin" />
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[200px] overflow-y-auto custom-scrollbar pr-2">
                {transforms.map((t) => {
                  const isSelected = selectedTransforms.has(t.id);
                  return (
                    <div 
                      key={t.id} 
                      onClick={() => toggleTransform(t.id)}
                      className={`flex items-start gap-3 p-2.5 rounded-lg border cursor-pointer transition-colors ${
                        isSelected 
                          ? 'bg-indigo-500/10 border-indigo-500/30' 
                          : 'bg-slate-800/50 border-slate-700/50 hover:border-slate-600'
                      }`}
                    >
                      <div className={`mt-0.5 flex items-center justify-center shrink-0 w-4 h-4 rounded border ${
                        isSelected ? 'bg-indigo-500 border-indigo-500 text-white' : 'border-slate-500'
                      }`}>
                        {isSelected && <Check className="w-3 h-3" />}
                      </div>
                      <div>
                        <div className={`text-sm font-medium ${isSelected ? 'text-indigo-200' : 'text-slate-300'}`}>
                          {t.name}
                        </div>
                        <div className="text-xs text-slate-500 mt-0.5">
                          {t.description}
                        </div>
                      </div>
                    </div>
                  );
                })}
                {transforms.length === 0 && !loading && (
                  <div className="text-xs text-slate-500 text-center p-4">No transforms available</div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-slate-800 bg-slate-900/80 flex items-center justify-between shrink-0">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-300 hover:text-white transition-colors"
          >
            Cancel
          </button>
          <button 
            onClick={() => {
              onStart(depth, maxEntities, Array.from(selectedTransforms));
              onClose();
            }}
            disabled={selectedTransforms.size === 0}
            className={`flex items-center gap-2 px-5 py-2 text-sm font-bold text-white rounded-lg transition-all ${
              selectedTransforms.size === 0 
                ? 'bg-slate-700 text-slate-400 cursor-not-allowed'
                : 'bg-indigo-600 hover:bg-indigo-500 shadow-lg shadow-indigo-500/20'
            }`}
          >
            <Play className="w-4 h-4" />
            Launch Investigation
          </button>
        </div>
      </div>
    </div>
  );
}
