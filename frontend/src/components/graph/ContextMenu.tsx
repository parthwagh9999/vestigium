import { useState, useEffect, useRef } from 'react';
import type { Node as FlowNode } from '@xyflow/react';
import apiClient from '@/api/client';
import {
  Play,
  Copy,
  Trash2,
  Pin,
  Maximize2,
  Tag,
  Loader2,
  ChevronRight,
  Sparkles,
} from 'lucide-react';

interface TransformItem {
  id: string;
  name: string;
  description: string;
  category: string;
}

interface ContextMenuProps {
  x: number;
  y: number;
  node: FlowNode;
  investigationId: string;
  onClose: () => void;
  onRunTransform: (transformId: string) => void;
  onDeleteNode: (nodeId: string) => void;
  onCenterNode: (node: FlowNode) => void;
}

export default function ContextMenu({
  x,
  y,
  node,
  investigationId,
  onClose,
  onRunTransform,
  onDeleteNode,
  onCenterNode,
}: ContextMenuProps) {
  const menuRef = useRef<HTMLDivElement>(null);
  const [transforms, setTransforms] = useState<TransformItem[]>([]);
  const [loadingTransforms, setLoadingTransforms] = useState(false);
  const [showTransformsSubmenu, setShowTransformsSubmenu] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        onClose();
      }
    };
    window.addEventListener('mousedown', handleClickOutside);
    return () => window.removeEventListener('mousedown', handleClickOutside);
  }, [onClose]);

  useEffect(() => {
    loadTransforms();
  }, [node]);

  const loadTransforms = async () => {
    const rawType = (node.data?.entityType as string) || 'custom';
    setLoadingTransforms(true);
    try {
      const { data } = await apiClient.get<TransformItem[]>(`/transforms?input_type=${rawType}`);
      setTransforms(data);
    } catch (err) {
      console.error('Failed to load context menu transforms:', err);
    } finally {
      setLoadingTransforms(false);
    }
  };

  const handleCopy = () => {
    const val = (node.data?.value as string) || (node.data?.label as string) || '';
    navigator.clipboard.writeText(val);
    setCopied(true);
    setTimeout(() => {
      setCopied(false);
      onClose();
    }, 800);
  };

  const label = String(node.data?.label || node.id);
  const entityType = String(node.data?.entityType || 'custom')
    .replace(/_/g, ' ')
    .toUpperCase();
  const color = (node.data?.color as string) || '#3b82f6';

  // Screen boundary clamping
  const menuWidth = 220;
  const menuHeight = 280;
  const clampedX = Math.min(x, window.innerWidth - menuWidth - 10);
  const clampedY = Math.min(y, window.innerHeight - menuHeight - 10);

  return (
    <div
      ref={menuRef}
      className="fixed z-50 w-56 glass shadow-2xl rounded-xl p-1.5 text-xs animate-fade-in border select-none"
      style={{
        top: clampedY,
        left: clampedX,
        borderColor: 'var(--color-vestigium-border)',
        backdropFilter: 'blur(16px)',
      }}
    >
      {/* Node Header */}
      <div className="px-2.5 py-2 mb-1 border-b" style={{ borderColor: 'var(--color-vestigium-border)' }}>
        <span className="text-[9px] font-bold tracking-wider uppercase block mb-0.5" style={{ color }}>
          {entityType}
        </span>
        <p className="font-semibold text-white truncate" title={label}>
          {label}
        </p>
      </div>

      {/* Menu Actions */}
      <div className="space-y-0.5 relative">
        {/* Transforms Submenu Trigger */}
        <div className="relative" onMouseEnter={() => setShowTransformsSubmenu(true)}>
          <button
            className="w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg hover:bg-blue-500/20 hover:text-blue-400 text-slate-200 text-left transition-colors"
          >
            <div className="flex items-center gap-2">
              <Sparkles className="w-3.5 h-3.5 text-blue-400" />
              <span>Run Transform</span>
            </div>
            <div className="flex items-center gap-1">
              <span className="text-[10px] bg-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded font-mono">
                {transforms.length}
              </span>
              <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            </div>
          </button>

          {/* Submenu Overlay */}
          {showTransformsSubmenu && (
            <div
              className="absolute left-full top-0 ml-1 w-64 glass shadow-2xl rounded-xl p-1.5 border space-y-1 animate-fade-in max-h-72 overflow-y-auto"
              style={{ borderColor: 'var(--color-vestigium-border)' }}
              onMouseLeave={() => setShowTransformsSubmenu(false)}
            >
              <div className="px-2 py-1 text-[10px] uppercase tracking-wider font-semibold text-slate-400 border-b border-slate-800">
                Available Transforms
              </div>
              {loadingTransforms ? (
                <div className="p-3 text-center text-slate-400 flex items-center justify-center gap-2">
                  <Loader2 className="w-3.5 h-3.5 animate-spin" /> Loading...
                </div>
              ) : transforms.length === 0 ? (
                <div className="p-2 text-center text-slate-500 text-[11px] italic">
                  No transforms for this type
                </div>
              ) : (
                Object.entries(
                  transforms.reduce((acc, t) => {
                    if (!acc[t.category]) acc[t.category] = [];
                    acc[t.category].push(t);
                    return acc;
                  }, {} as Record<string, TransformItem[]>)
                ).map(([category, cats]) => (
                  <div key={category} className="mb-2 last:mb-0">
                    <div className="px-2 py-1 text-[9px] uppercase tracking-widest font-bold text-slate-500 bg-slate-900/50">
                      {category}
                    </div>
                    {cats.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => {
                          onRunTransform(t.id);
                          onClose();
                        }}
                        className="w-full text-left p-2 rounded-lg hover:bg-blue-600/20 hover:border-blue-500/40 border border-transparent transition-all group"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-white text-[11px] group-hover:text-blue-300">
                            {t.name}
                          </span>
                          <Play className="w-3 h-3 text-blue-400 opacity-0 group-hover:opacity-100 transition-opacity" />
                        </div>
                        <p className="text-[10px] text-slate-400 line-clamp-1 mt-0.5">{t.description}</p>
                      </button>
                    ))}
                  </div>
                ))
              )}
            </div>
          )}
        </div>

        {/* Copy Value */}
        <button
          onClick={handleCopy}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200 text-left transition-colors"
        >
          <Copy className="w-3.5 h-3.5 text-slate-400" />
          <span>{copied ? 'Copied!' : 'Copy Value'}</span>
        </button>

        {/* Center Node */}
        <button
          onClick={() => {
            onCenterNode(node);
            onClose();
          }}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200 text-left transition-colors"
        >
          <Maximize2 className="w-3.5 h-3.5 text-slate-400" />
          <span>Center View</span>
        </button>

        <div className="my-1 border-t" style={{ borderColor: 'var(--color-vestigium-border)' }} />

        {/* Path Exploration */}
        <div className="px-2.5 py-1 text-[9px] uppercase tracking-wider font-semibold text-slate-500">
          Path Exploration
        </div>
        <button
          onClick={() => {
            console.log('Show Ancestors for', node.id);
            onClose();
          }}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200 text-left transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5 text-slate-400" />
          <span>Show Ancestors</span>
        </button>
        <button
          onClick={() => {
            console.log('Show Descendants for', node.id);
            onClose();
          }}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200 text-left transition-colors"
        >
          <Sparkles className="w-3.5 h-3.5 text-slate-400" />
          <span>Show Descendants</span>
        </button>

        {/* Declutter */}
        <div className="px-2.5 py-1 mt-1 text-[9px] uppercase tracking-wider font-semibold text-slate-500">
          Declutter
        </div>
        <button
          onClick={() => {
            console.log('Hide isolated nodes');
            onClose();
          }}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-slate-800 text-slate-200 text-left transition-colors"
        >
          <Tag className="w-3.5 h-3.5 text-slate-400" />
          <span>Hide Isolated Nodes</span>
        </button>

        <div className="my-1 border-t" style={{ borderColor: 'var(--color-vestigium-border)' }} />

        {/* Delete Entity */}
        <button
          onClick={() => {
            onDeleteNode(node.id);
            onClose();
          }}
          className="w-full flex items-center gap-2 px-2.5 py-1.5 rounded-lg hover:bg-red-500/20 text-red-400 text-left transition-colors"
        >
          <Trash2 className="w-3.5 h-3.5 text-red-400" />
          <span>Delete Entity</span>
        </button>
      </div>
    </div>
  );
}
