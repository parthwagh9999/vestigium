import type { Node, Edge } from '@xyflow/react';
import { Grid, Link2, Check, Minus } from 'lucide-react';

interface MatrixViewProps {
  nodes: Node[];
  edges: Edge[];
}

export default function MatrixView({ nodes, edges }: MatrixViewProps) {
  // Build relationship lookup set
  const relSet = new Set<string>();
  edges.forEach((e) => {
    relSet.add(`${e.source}->${e.target}`);
    relSet.add(`${e.target}->${e.source}`);
  });

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden p-4 select-none">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Grid className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Relationship Matrix Grid</h2>
        </div>
        <span className="badge bg-purple-500/10 text-purple-400 border border-purple-500/20">
          {nodes.length} x {nodes.length} Matrix
        </span>
      </div>

      <div className="flex-1 border border-slate-800 rounded bg-slate-900 overflow-auto">
        {nodes.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-500 italic">No entities to construct matrix grid.</div>
        ) : (
          <table className="soc-table border-collapse">
            <thead>
              <tr>
                <th className="sticky left-0 top-0 z-20 bg-slate-950 border-r border-slate-800">Entity Matrix</th>
                {nodes.map((n) => (
                  <th key={n.id} className="text-center font-mono text-[10px] truncate max-w-[100px]" title={String(n.data?.label)}>
                    {String(n.data?.label || n.id)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {nodes.map((rowNode) => (
                <tr key={rowNode.id}>
                  <td className="sticky left-0 z-10 bg-slate-950 font-mono text-xs font-semibold text-white border-r border-slate-800 truncate max-w-[140px]">
                    {String(rowNode.data?.label || rowNode.id)}
                  </td>
                  {nodes.map((colNode) => {
                    const isSame = rowNode.id === colNode.id;
                    const isConnected = relSet.has(`${rowNode.id}->${colNode.id}`);
                    return (
                      <td key={colNode.id} className="text-center p-2 border border-slate-800/60">
                        {isSame ? (
                          <div className="w-2 h-2 rounded-full bg-slate-700 mx-auto" />
                        ) : isConnected ? (
                          <div className="w-5 h-5 rounded bg-blue-600/30 border border-blue-500/50 text-blue-400 flex items-center justify-center mx-auto">
                            <Check className="w-3 h-3 stroke-[3]" />
                          </div>
                        ) : (
                          <span className="text-slate-700">-</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
