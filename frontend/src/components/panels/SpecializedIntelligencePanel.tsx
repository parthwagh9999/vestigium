import React from 'react';
import { Globe, Server, User, Shield, Key, Database, Activity, ExternalLink } from 'lucide-react';

interface SpecializedPanelProps {
  entityType: string;
  properties: Record<string, any>;
}

export default function SpecializedIntelligencePanel({ entityType, properties }: SpecializedPanelProps) {
  
  if (entityType === 'ip_address') {
    return (
      <div className="space-y-4">
        <h4 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
          <Server className="w-3.5 h-3.5" /> IP Intelligence
        </h4>
        <div className="grid grid-cols-2 gap-2">
          <div className="bg-slate-900/50 border border-slate-800 rounded p-3">
            <span className="text-[9px] text-slate-500 uppercase block mb-1">ASN / ISP</span>
            <span className="text-xs text-blue-400 font-mono">{properties.asn || 'Unknown ASN'}</span>
            <p className="text-[10px] text-slate-400 mt-0.5">{properties.isp || 'Unknown ISP'}</p>
          </div>
          <div className="bg-slate-900/50 border border-slate-800 rounded p-3">
            <span className="text-[9px] text-slate-500 uppercase block mb-1">Geolocation</span>
            <span className="text-xs text-slate-200">{properties.country || 'Unknown'}, {properties.city || 'Unknown'}</span>
          </div>
          <div className="col-span-2 bg-slate-900/50 border border-slate-800 rounded p-3">
            <span className="text-[9px] text-slate-500 uppercase block mb-1">Threat Score</span>
            <div className="flex items-center gap-2 mt-1">
              <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                <div 
                  className="h-full rounded-full" 
                  style={{ 
                    width: `${properties.threat_score || 0}%`, 
                    backgroundColor: properties.threat_score > 50 ? '#ef4444' : properties.threat_score > 20 ? '#f59e0b' : '#10b981' 
                  }} 
                />
              </div>
              <span className="text-xs font-mono text-slate-300">{properties.threat_score || 0}/100</span>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (entityType === 'domain' || entityType === 'dns_record') {
    return (
      <div className="space-y-4">
        <h4 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
          <Globe className="w-3.5 h-3.5" /> Domain Intelligence
        </h4>
        <div className="bg-slate-900/50 border border-slate-800 rounded p-3 space-y-3">
          {properties.registrar && (
            <div>
              <span className="text-[9px] text-slate-500 uppercase block">Registrar</span>
              <span className="text-xs text-slate-200">{properties.registrar}</span>
            </div>
          )}
          {properties.creation_date && (
            <div>
              <span className="text-[9px] text-slate-500 uppercase block">Creation Date</span>
              <span className="text-xs text-slate-200 font-mono">{properties.creation_date}</span>
            </div>
          )}
          {properties.nameservers && (
            <div>
              <span className="text-[9px] text-slate-500 uppercase block">Nameservers</span>
              <div className="flex flex-col gap-1 mt-1">
                {(Array.isArray(properties.nameservers) ? properties.nameservers : properties.nameservers.split(',')).map((ns: string, i: number) => (
                  <span key={i} className="text-[10px] text-blue-400 font-mono">{ns.trim()}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (entityType === 'web_technology') {
    return (
      <div className="space-y-4">
        <h4 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
          <Activity className="w-3.5 h-3.5" /> Technology Profile
        </h4>
        <div className="bg-slate-900/50 border border-slate-800 rounded p-3">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="text-sm font-bold text-slate-200">{properties.vendor || 'Unknown Vendor'}</span>
              <span className="text-xs text-slate-400 ml-2">{properties.product || 'Unknown Product'}</span>
            </div>
            {properties.version && (
              <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded font-mono">
                v{properties.version}
              </span>
            )}
          </div>
          {properties.cve_count > 0 && (
            <div className="mt-3 p-2 bg-red-500/10 border border-red-500/20 rounded flex items-center gap-2">
              <Shield className="w-3 h-3 text-red-400" />
              <span className="text-[10px] text-red-400">Known Vulnerabilities: {properties.cve_count}</span>
            </div>
          )}
        </div>
      </div>
    );
  }

  if (entityType === 'social_profile') {
    return (
      <div className="space-y-4">
        <h4 className="text-[10px] font-mono text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-2">
          <User className="w-3.5 h-3.5" /> Social Profile Identity
        </h4>
        <div className="bg-slate-900/50 border border-slate-800 rounded p-3">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-bold text-slate-200">{properties.network || 'Unknown Network'}</span>
            <span className={`text-[9px] px-2 py-0.5 rounded uppercase font-bold tracking-wider ${
              properties.status === 'FOUND' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' :
              properties.status === 'RATE_LIMITED' ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' :
              'bg-slate-800 text-slate-400 border border-slate-700'
            }`}>
              {properties.status || 'UNKNOWN'}
            </span>
          </div>
          {properties.url && (
            <a href={properties.url} target="_blank" rel="noreferrer" className="text-xs text-blue-400 hover:underline flex items-center gap-1 mt-2">
              <ExternalLink className="w-3 h-3" /> View Profile
            </a>
          )}
        </div>
      </div>
    );
  }

  // Fallback for types that don't have a specialized view yet, 
  // but we return null so the generic property renderer handles it.
  return null;
}
