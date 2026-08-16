import { useState, useEffect } from 'react';
import type { Node } from '@xyflow/react';
import apiClient from '@/api/client';
import { useConsoleStore } from '@/stores/consoleStore';
import { X, ExternalLink, Copy, Trash2, Tag, MessageSquare, Clock, Check, Play, Loader2, AlertTriangle } from 'lucide-react';
import SpecializedIntelligencePanel from './SpecializedIntelligencePanel';

interface TransformItem {
  id: string;
  name: string;
  description: string;
  category: string;
  input_entity_types: string[];
  output_entity_types: string[];
}

interface EntityPanelProps {
  selectedNode: Node | null;
  investigationId: string;
  onTransformExecuted?: (nodeId?: string) => void;
}

export default function EntityPanel({ selectedNode, investigationId, onTransformExecuted }: EntityPanelProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'transforms' | 'evidence' | 'notes'>('details');
  const [notes, setNotes] = useState('');
  const [copied, setCopied] = useState(false);

  const [evidence, setEvidence] = useState<any[]>([]);
  const [loadingEvidence, setLoadingEvidence] = useState(false);
  const [contradictions, setContradictions] = useState<any[]>([]);

  const [transforms, setTransforms] = useState<TransformItem[]>([]);
  const [loadingTransforms, setLoadingTransforms] = useState(false);
  const [executingTransformId, setExecutingTransformId] = useState<string | null>(null);
  const [transformError, setTransformError] = useState<string | null>(null);

  useEffect(() => {
    if (selectedNode?.data?.notes) {
      setNotes(selectedNode.data.notes as string);
    } else {
      setNotes('');
    }

    if (selectedNode) {
      loadTransforms();
      loadEvidence();
      loadContradictions();
    }
  }, [selectedNode]);

  const loadContradictions = async () => {
    if (!selectedNode) return;
    try {
      const { data } = await apiClient.get<any>(`/evidence/entity/${selectedNode.id}/contradictions`);
      setContradictions(data.conflicts || []);
    } catch (err) {
      console.error('Failed to load contradictions:', err);
    }
  };

  const loadEvidence = async () => {
    if (!selectedNode || !investigationId) return;
    setLoadingEvidence(true);
    try {
      const { data } = await apiClient.get<any>(`/evidence?investigation_id=${investigationId}&entity_id=${selectedNode.id}`);
      setEvidence(data.items || []);
    } catch (err) {
      console.error('Failed to load evidence:', err);
    } finally {
      setLoadingEvidence(false);
    }
  };

  const loadTransforms = async () => {
    if (!selectedNode) return;
    const rawType = (selectedNode.data?.entityType as string) || 'custom';
    setLoadingTransforms(true);
    setTransformError(null);
    try {
      const { data } = await apiClient.get<TransformItem[]>(`/transforms?input_type=${rawType}`);
      setTransforms(data);
    } catch (err) {
      console.error('Failed to load transforms:', err);
    } finally {
      setLoadingTransforms(false);
    }
  };

  const handleRunTransform = async (transformId: string) => {
    if (!selectedNode || !investigationId) return;
    setExecutingTransformId(transformId);
    setTransformError(null);

    const targetVal = (selectedNode.data?.value as string) || (selectedNode.data?.label as string) || 'Target';
    const queueId = `${transformId}-${Date.now()}`;
    const tStart = performance.now();

    useConsoleStore.getState().addQueueItem({
      id: queueId,
      transformId,
      targetValue: targetVal,
      status: 'running',
    });
    useConsoleStore.getState().addLog('INFO', `Executing ${transformId} on ${targetVal}...`);

    try {
      const { data } = await apiClient.post('/transforms/execute', {
        investigation_id: investigationId,
        transform_id: transformId,
        input_entity_id: selectedNode.id,
      });

      const dur = (performance.now() - tStart) / 1000;
      useConsoleStore.getState().updateQueueItem(queueId, {
        status: 'completed',
        durationSeconds: dur,
        entitiesCreated: data.entities_created || 0,
        relationshipsCreated: data.relationships_created || 0,
      });
      useConsoleStore.getState().addLog(
        'SUCCESS',
        `${transformId} completed: +${data.entities_created || 0} entities, +${data.relationships_created || 0} relationships`,
      );

      if (onTransformExecuted) {
        onTransformExecuted(selectedNode.id);
      }
    } catch (err: any) {
      const dur = (performance.now() - tStart) / 1000;
      useConsoleStore.getState().updateQueueItem(queueId, {
        status: 'failed',
        durationSeconds: dur,
      });
      const msg = err.response?.data?.message || err.message || 'Transform execution failed';
      useConsoleStore.getState().addLog('ERROR', `Failed to execute ${transformId}: ${msg}`);
      setTransformError(msg);
    } finally {
      setExecutingTransformId(null);
    }
  };

  const copyValue = () => {
    if (selectedNode?.data?.value) {
      navigator.clipboard.writeText(selectedNode.data.value as string);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!selectedNode) {
    return (
      <div className="p-6 flex flex-col items-center justify-center h-full">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'var(--color-vestigium-surface-2)', border: '1px solid var(--color-vestigium-border)' }}>
          <Tag className="w-6 h-6" style={{ color: 'var(--color-vestigium-text-muted)' }} />
        </div>
        <p className="text-sm font-medium text-white mb-1">No entity selected</p>
        <p className="text-xs text-center" style={{ color: 'var(--color-vestigium-text-muted)' }}>
          Click on an entity in the graph to view its details
        </p>
      </div>
    );
  }

  const data = selectedNode.data || {};
  const rawType = (data.entityType as string) || 'custom';
  const entityTypeLabel = rawType.replace(/_/g, ' ').replace(/\b\w/g, (c: string) => c.toUpperCase());
  const color = (data.color as string) || '#3b82f6';
  const properties = (data.properties as Record<string, any>) || {};

  const tabs = [
    { key: 'details', label: 'Details' },
    { key: 'transforms', label: 'Transforms' },
    { key: 'evidence', label: 'Evidence' },
    { key: 'notes', label: 'Notes' },
  ] as const;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b" style={{ borderColor: 'var(--color-vestigium-border)' }}>
        <div className="flex items-center justify-between mb-3">
          <span className="text-[10px] font-semibold uppercase tracking-wider" style={{ color }}>
            {entityTypeLabel}
          </span>
          <div className="flex items-center gap-1">
            <button onClick={copyValue} className="btn btn-ghost p-1" title="Copy value">
              {copied ? <Check className="w-3.5 h-3.5 text-green-400" /> : <Copy className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>
        <h3 className="text-base font-bold text-white truncate" title={String(data.label)}>
          {String(data.label)}
        </h3>
        {Boolean(data.value) && data.value !== data.label && (
          <p className="text-xs font-mono mt-1 truncate" style={{ color: 'var(--color-vestigium-text-dim)' }}>
            {String(data.value)}
          </p>
        )}

        {/* Confidence */}
        <div className="mt-3 flex items-center gap-2">
          <span className="text-[10px] uppercase tracking-wide" style={{ color: 'var(--color-vestigium-text-muted)' }}>
            Confidence
          </span>
          <div className="flex-1 h-1.5 rounded-full" style={{ background: 'var(--color-vestigium-surface)' }}>
            <div
              className="h-full rounded-full"
              style={{
                width: `${((data.confidence as number) ?? 1.0) * 100}%`,
                background: color,
              }}
            />
          </div>
          <span className="text-xs font-mono" style={{ color: 'var(--color-vestigium-text-dim)' }}>
            {Math.round(((data.confidence as number) ?? 1.0) * 100)}%
          </span>
        </div>
        {/* Contradiction Alert */}
        {contradictions.length > 0 && (
          <div className="mt-3 p-2 rounded bg-red-500/10 border border-red-500/30 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div>
              <span className="text-xs font-bold text-red-400">CONFLICT DETECTED</span>
              <p className="text-[10px] text-red-300/80 mt-0.5">
                {contradictions.length} contradictory claims found across sources. Check Evidence tab.
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b" style={{ borderColor: 'var(--color-vestigium-border)' }}>
        {tabs.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className="flex-1 py-2.5 text-xs font-medium transition-colors relative"
            style={{
              color: activeTab === tab.key ? 'var(--color-vestigium-accent)' : 'var(--color-vestigium-text-muted)',
            }}
          >
            {tab.label}
            {activeTab === tab.key && (
              <div className="absolute bottom-0 left-2 right-2 h-0.5 rounded-full" style={{ background: 'var(--color-vestigium-accent)' }} />
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {activeTab === 'details' && (
          <div className="space-y-4 animate-fade-in">
            {/* Source */}
            {Boolean(data.source) && (
              <div>
                <label className="text-[10px] uppercase tracking-wider font-medium block mb-1" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                  Source
                </label>
                <p className="text-xs" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                  {String(data.source)}
                </p>
              </div>
            )}

            {/* Specialized Intelligence Panel (If Applicable) */}
            <SpecializedIntelligencePanel entityType={rawType} properties={properties} />

            {/* Generic Properties */}
            {Object.keys(properties).length > 0 && (
              <div>
                <label className="text-[10px] uppercase tracking-wider font-medium block mb-2" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                  Properties
                </label>
                <div className="space-y-2">
                  {Object.entries(properties).map(([key, value]) => (
                    <div key={key} className="glass-subtle p-2.5 rounded-lg">
                      <span className="text-[10px] uppercase tracking-wider block mb-0.5" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                        {key.replace(/_/g, ' ')}
                      </span>
                      <span className="text-xs text-white font-mono break-all">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Position */}
            <div>
              <label className="text-[10px] uppercase tracking-wider font-medium block mb-1" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                Position
              </label>
              <p className="text-xs font-mono" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                x: {Math.round(selectedNode.position.x)}, y: {Math.round(selectedNode.position.y)}
              </p>
            </div>
          </div>
        )}

        {activeTab === 'transforms' && (
          <div className="space-y-3 animate-fade-in">
            <p className="text-xs" style={{ color: 'var(--color-vestigium-text-dim)' }}>
              Available transforms for <span className="text-white font-medium">{entityTypeLabel}</span>:
            </p>

            {transformError && (
              <div className="p-2.5 rounded text-xs bg-red-500/10 border border-red-500/20 text-red-400">
                {transformError}
              </div>
            )}

            {loadingTransforms ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--color-vestigium-accent)' }} />
              </div>
            ) : transforms.length === 0 ? (
              <p className="text-xs italic py-4 text-center" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                No transforms available for this entity type.
              </p>
            ) : (
              <>
                <button
                  onClick={async () => {
                    setExecutingTransformId('orchestrator');
                    useConsoleStore.getState().addLog('INFO', `Running all safe OSINT modules against ${(selectedNode.data?.value as string) || (selectedNode.data?.label as string)}...`);
                    try {
                      const { data } = await apiClient.post(`/investigations/${investigationId}/orchestrate`, { entity_id: selectedNode.id });
                      if (data?.results) {
                        data.results.forEach((r: any) => {
                          if (r.status === 'success') {
                            useConsoleStore.getState().addLog('SUCCESS', `Completed ${r.name || r.id}: +${r.entities_created || 0} entities, +${r.relationships_created || 0} relationships`);
                          }
                        });
                      }
                      if (onTransformExecuted) onTransformExecuted(selectedNode.id);
                    } catch (err: any) {
                      const msg = err?.response?.data?.message || err?.message || 'Orchestration failed';
                      useConsoleStore.getState().addLog('ERROR', `Orchestration error: ${msg}`);
                    } finally {
                      setExecutingTransformId(null);
                    }
                  }}
                  disabled={executingTransformId !== null}
                  className="w-full btn btn-primary h-8 text-xs flex items-center justify-center gap-2 mb-4 bg-emerald-600 hover:bg-emerald-500 text-white border-none shadow-lg shadow-emerald-500/20"
                >
                  {executingTransformId === 'orchestrator' ? (
                    <><Loader2 className="w-3.5 h-3.5 animate-spin" /> Orchestrating all modules...</>
                  ) : (
                    <><Play className="w-3.5 h-3.5 fill-current" /> Run All Safe OSINT</>
                  )}
                </button>
                {transforms.map((t) => (
                  <div key={t.id} className="glass-subtle p-3 rounded-lg flex flex-col gap-2">
                    <div>
                      <h4 className="text-xs font-semibold text-white">{t.name}</h4>
                      <p className="text-[11px] mt-0.5" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                        {t.description}
                      </p>
                    </div>
                    <button
                      onClick={() => handleRunTransform(t.id)}
                      disabled={executingTransformId !== null}
                      className="btn btn-secondary h-7 text-xs px-3 self-end border border-slate-700"
                    >
                      {executingTransformId === t.id ? (
                        <>
                          <Loader2 className="w-3 h-3 animate-spin" /> Running...
                        </>
                      ) : (
                        <>
                          Run Transform
                        </>
                      )}
                    </button>
                  </div>
                ))}
              </>
            )}
          </div>
        )}

        {activeTab === 'evidence' && (
          <div className="space-y-3 animate-fade-in">
            {loadingEvidence ? (
              <div className="flex items-center justify-center py-6">
                <Loader2 className="w-5 h-5 animate-spin" style={{ color: 'var(--color-vestigium-accent)' }} />
              </div>
            ) : evidence.length === 0 ? (
              <p className="text-xs italic py-4 text-center" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                No evidence records found for this entity.
              </p>
            ) : (
              evidence.map((item) => (
                <div key={item.id} className="glass-subtle p-3 rounded-lg flex flex-col gap-2">
                  <div className="flex justify-between items-start">
                    <h4 className="text-xs font-semibold text-white">{item.title}</h4>
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">
                      Conf: {Math.round((item.confidence || 1.0) * 100)}%
                    </span>
                  </div>
                  <div className="text-[10px] space-y-1 mt-1">
                    <p style={{ color: 'var(--color-vestigium-text-dim)' }}>
                      <span className="font-medium text-slate-400">Source:</span> {item.source || 'Manual/Unknown'}
                    </p>
                    <p style={{ color: 'var(--color-vestigium-text-dim)' }}>
                      <span className="font-medium text-slate-400">Type:</span> {item.evidence_type}
                    </p>
                    <p style={{ color: 'var(--color-vestigium-text-dim)' }}>
                      <span className="font-medium text-slate-400">Time:</span> {new Date(item.created_at).toLocaleString()}
                    </p>
                    {item.raw_data && (
                      <div className="mt-2">
                        <span className="font-medium text-slate-400 block mb-1">Raw Result:</span>
                        <div className="max-h-24 overflow-y-auto bg-black/40 rounded p-1.5">
                          <pre className="text-[9px] text-emerald-400/80 font-mono whitespace-pre-wrap break-all">
                            {typeof item.raw_data === 'object' ? JSON.stringify(item.raw_data, null, 2) : item.raw_data}
                          </pre>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === 'notes' && (
          <div className="animate-fade-in">
            <textarea
              className="input min-h-[200px] resize-none text-xs"
              placeholder="Add investigation notes for this entity..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
            />
          </div>
        )}
      </div>
    </div>
  );
}
