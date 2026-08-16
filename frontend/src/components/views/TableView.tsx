import { useState } from 'react';
import type { Node, Edge } from '@xyflow/react';
import { Search, Download, Filter, Eye, Trash2, ArrowUpDown } from 'lucide-react';

interface TableViewProps {
  nodes: Node[];
  edges: Edge[];
  onSelectNode: (node: Node) => void;
  onDeleteNode: (nodeId: string) => void;
}

export default function TableView({ nodes, edges, onSelectNode, onDeleteNode }: TableViewProps) {
  const [activeTab, setActiveTab] = useState<'entities' | 'relationships'>('entities');
  const [search, setSearch] = useState('');

  const filteredNodes = nodes.filter((n) => {
    const val = String(n.data?.value || n.data?.label || '').toLowerCase();
    const type = String(n.data?.entityType || '').toLowerCase();
    return val.includes(search.toLowerCase()) || type.includes(search.toLowerCase());
  });

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden p-4">
      {/* Header Bar */}
      <div className="flex items-center justify-between mb-3 gap-3">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('entities')}
            className={`btn ${activeTab === 'entities' ? 'btn-primary' : 'btn-secondary'} text-xs h-8 px-3`}
          >
            Entities ({nodes.length})
          </button>
          <button
            onClick={() => setActiveTab('relationships')}
            className={`btn ${activeTab === 'relationships' ? 'btn-primary' : 'btn-secondary'} text-xs h-8 px-3`}
          >
            Relationships ({edges.length})
          </button>
        </div>

        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              className="input pl-8 text-xs w-64 h-8"
              placeholder="Search table data..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
        </div>
      </div>

      {/* Table Container */}
      <div className="flex-1 border border-slate-800 rounded bg-slate-900 overflow-y-auto">
        {activeTab === 'entities' ? (
          <table className="soc-table">
            <thead>
              <tr>
                <th>Type</th>
                <th>Value</th>
                <th>Confidence</th>
                <th>Source</th>
                <th>Position (X, Y)</th>
                <th className="text-right">Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredNodes.length === 0 ? (
                <tr>
                  <td colSpan={6} className="text-center text-slate-500 py-8 italic">
                    No matching entities in investigation.
                  </td>
                </tr>
              ) : (
                filteredNodes.map((n) => {
                  const type = String(n.data?.entityType || 'custom').toUpperCase();
                  const val = String(n.data?.value || n.data?.label || n.id);
                  const conf = Math.round(((n.data?.confidence as number) ?? 1.0) * 100);
                  const color = (n.data?.color as string) || '#3b82f6';
                  return (
                    <tr key={n.id}>
                      <td>
                        <span className="badge" style={{ background: `${color}20`, color }}>
                          {type}
                        </span>
                      </td>
                      <td className="font-mono text-white font-semibold">{val}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-slate-800">
                            <div className="h-full rounded-full" style={{ width: `${conf}%`, background: color }} />
                          </div>
                          <span className="font-mono text-[11px] text-slate-400">{conf}%</span>
                        </div>
                      </td>
                      <td className="text-slate-400">{String(n.data?.source || 'Manual Input')}</td>
                      <td className="font-mono text-slate-400">
                        {Math.round(n.position.x)}, {Math.round(n.position.y)}
                      </td>
                      <td className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <button
                            onClick={() => onSelectNode(n)}
                            className="btn btn-ghost p-1 text-slate-400 hover:text-blue-400"
                            title="Inspect Entity"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => onDeleteNode(n.id)}
                            className="btn btn-ghost p-1 text-slate-400 hover:text-red-400"
                            title="Delete Entity"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        ) : (
          <table className="soc-table">
            <thead>
              <tr>
                <th>Source Entity</th>
                <th>Relationship Type</th>
                <th>Target Entity</th>
                <th>Confidence</th>
              </tr>
            </thead>
            <tbody>
              {edges.map((e) => (
                <tr key={e.id}>
                  <td className="font-mono text-white">{e.source}</td>
                  <td>
                    <span className="badge bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      {String(e.label || 'related_to')}
                    </span>
                  </td>
                  <td className="font-mono text-white">{e.target}</td>
                  <td className="font-mono text-slate-400">100%</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
