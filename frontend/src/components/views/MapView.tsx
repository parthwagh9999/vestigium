import type { Node } from '@xyflow/react';
import { Globe, MapPin, Server, Navigation, Shield } from 'lucide-react';

interface MapViewProps {
  nodes: Node[];
  onSelectNode: (node: Node) => void;
}

export default function MapView({ nodes, onSelectNode }: MapViewProps) {
  // Filter nodes that have location/country or IP address data
  const geoNodes = nodes.filter((n) => {
    const t = String(n.data?.entityType || '');
    const props = (n.data?.properties as Record<string, any>) || {};
    return t === 'ip_address' || t === 'country' || t === 'city' || props.lat;
  });

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden p-4 select-none">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Globe className="w-4 h-4 text-cyan-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Geographical Intelligence Map</h2>
        </div>
        <span className="badge bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{geoNodes.length} Mapped Entities</span>
      </div>

      <div className="flex-1 rounded border border-slate-800 bg-slate-900/80 relative flex flex-col items-center justify-center overflow-hidden">
        {/* World Grid Visual SVG Overlay */}
        <svg className="absolute inset-0 w-full h-full opacity-15 pointer-events-none stroke-slate-700" strokeWidth="0.5">
          <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>

        {geoNodes.length === 0 ? (
          <div className="text-center z-10 p-6 max-w-sm">
            <div className="w-12 h-12 rounded bg-slate-800 border border-slate-700 flex items-center justify-center mx-auto mb-3 text-cyan-400">
              <MapPin className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-white mb-1">No Geolocation Entities Yet</h3>
            <p className="text-xs text-slate-400">
              Run an IP Geolocation transform on target IP addresses to plot host locations and AS networks on the map.
            </p>
          </div>
        ) : (
          <div className="w-full h-full p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 overflow-y-auto z-10">
            {geoNodes.map((node) => {
              const label = String(node.data?.label || node.data?.value || node.id);
              const type = String(node.data?.entityType || 'location').toUpperCase();
              const props = (node.data?.properties as Record<string, any>) || {};
              const lat = props.lat ?? '37.7749';
              const lon = props.lon ?? '-122.4194';

              return (
                <div
                  key={node.id}
                  onClick={() => onSelectNode(node)}
                  className="p-3 rounded bg-slate-950 border border-slate-800 hover:border-cyan-500/50 transition-all cursor-pointer space-y-2 group"
                >
                  <div className="flex items-center justify-between">
                    <span className="badge bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">{type}</span>
                    <MapPin className="w-3.5 h-3.5 text-cyan-400 group-hover:scale-125 transition-transform" />
                  </div>
                  <h4 className="text-xs font-mono font-bold text-white group-hover:text-cyan-300 truncate">{label}</h4>
                  <div className="text-[11px] font-mono text-slate-400 flex items-center justify-between border-t border-slate-800/80 pt-1.5">
                    <span>Coordinates:</span>
                    <span className="text-slate-200">{lat}, {lon}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
