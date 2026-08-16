import { useState } from 'react';
import {
  Boxes,
  Zap,
  Bookmark,
  FileText,
  Settings,
  ShieldAlert,
  Search,
  Eye,
  Plus
} from 'lucide-react';
import EntityPalette from '@/components/panels/EntityPalette';
import EntityVisibilityPanel from '@/components/panels/EntityVisibilityPanel';

interface LeftNavigationSidebarProps {
  onSelectEntityType: (type: string) => void;
  onRunTransform: (transformId: string) => void;
  isOpen: boolean;
  onToggle: () => void;
}

export default function LeftNavigationSidebar({
  onSelectEntityType,
  onRunTransform,
  isOpen,
  onToggle,
}: LeftNavigationSidebarProps) {
  const [activeTab, setActiveTab] = useState<'entities' | 'visibility' | 'transforms' | 'evidence' | 'saved_queries' | 'reports'>('entities');
  const [transformFilter, setTransformFilter] = useState('');

  const activityItems = [
    { id: 'entities', label: 'Entity Palette', icon: Boxes },
    { id: 'visibility', label: 'Entity Visibility', icon: Eye },
    { id: 'transforms', label: 'Transform Hub', icon: Zap },
    { id: 'evidence', label: 'Evidence Locker', icon: ShieldAlert },
    { id: 'saved_queries', label: 'Saved Queries', icon: Bookmark },
    { id: 'reports', label: 'Case Files & Reports', icon: FileText },
  ] as const;

  const transforms = [
    { id: 'builtin.dns_lookup', name: 'DNS Record Lookup', category: 'Infrastructure', desc: 'Resolves A, MX, NS, and TXT records' },
    { id: 'builtin.ip_geolocation', name: 'IP Geolocation Lookup', category: 'Geolocation', desc: 'Country, City, ISP, and ASN query' },
    { id: 'builtin.whois_lookup', name: 'WHOIS Domain Query', category: 'Registration', desc: 'Domain registrar and registrant emails' },
    { id: 'builtin.shodan_internetdb', name: 'Shodan InternetDB Query', category: 'Threat Intel', desc: 'Open ports and CVE vulnerabilities' },
    { id: 'builtin.subdomain_enum', name: 'Subdomain Search (CT Logs)', category: 'Infrastructure', desc: 'Discovers subdomains via crt.sh' },
    { id: 'builtin.reverse_ip_lookup', name: 'Reverse IP Lookup', category: 'Infrastructure', desc: 'Co-hosted domains on IP' },
    { id: 'builtin.username_social_search', name: 'Social Media Enumeration', category: 'Social Intel', desc: 'Presence search across 10+ networks' },
    { id: 'builtin.web_tech_stack', name: 'Web Tech Stack Scraper', category: 'Web OSINT', desc: 'Headers, server, and tech stack detection' },
    { id: 'builtin.bitcoin_wallet_lookup', name: 'Bitcoin Wallet Explorer', category: 'Crypto', desc: 'BTC balance and transaction counts' },
    { id: 'builtin.reverse_dns', name: 'Reverse DNS (PTR)', category: 'Infrastructure', desc: 'PTR record lookup for IP addresses' },
  ];

  return (
    <div className="flex h-full glass bg-slate-950/60 backdrop-blur-xl border-r border-slate-700/50 select-none z-20 shrink-0 transition-all duration-300">
      {/* Activity Bar (VS Code style) */}
      <div className="w-14 bg-slate-950/40 border-r border-slate-700/30 flex flex-col items-center justify-between py-3 shrink-0 shadow-[4px_0_24px_rgba(0,0,0,0.5)]">
        <div className="flex flex-col items-center gap-3 w-full">
          {activityItems.map((item) => {
            const Icon = item.icon;
            const active = isOpen && activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  if (isOpen && activeTab === item.id) {
                    onToggle();
                  } else {
                    setActiveTab(item.id);
                    if (!isOpen) onToggle();
                  }
                }}
                className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-300 relative group ${
                  active
                    ? 'bg-blue-500/20 text-blue-400 shadow-[inset_0_0_12px_rgba(59,130,246,0.3)] border border-blue-500/50'
                    : 'text-slate-400 hover:text-blue-300 hover:bg-slate-800/80 hover:shadow-[0_0_15px_rgba(59,130,246,0.2)]'
                }`}
                title={item.label}
              >
                <Icon className={`w-5 h-5 ${active ? 'drop-shadow-[0_0_8px_rgba(59,130,246,0.8)]' : 'group-hover:scale-110 transition-transform'}`} />
                {active && (
                  <div className="absolute left-0 top-2 bottom-2 w-1 bg-blue-500 rounded-r shadow-[0_0_10px_#3b82f6]" />
                )}
              </button>
            );
          })}
        </div>

        <div className="flex flex-col items-center gap-2">
          <button className="w-10 h-10 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800/80 hover:shadow-[0_0_10px_rgba(255,255,255,0.1)] flex items-center justify-center transition-all duration-300 group" title="Settings">
            <Settings className="w-5 h-5 group-hover:rotate-90 transition-transform duration-500" />
          </button>
        </div>
      </div>

      {/* Expandable Drawer Panel */}
      <div className={`transition-all duration-300 ease-in-out overflow-hidden flex flex-col h-full bg-slate-900/60 border-r border-slate-700/50 shadow-[4px_0_24px_rgba(0,0,0,0.3)] ${isOpen ? 'w-72 opacity-100' : 'w-0 opacity-0 border-r-0'}`}>
        {isOpen && (
          <>
          {activeTab === 'entities' && (
            <EntityPalette onSelectType={onSelectEntityType} />
          )}

          {activeTab === 'visibility' && (
            <EntityVisibilityPanel />
          )}

          {activeTab === 'transforms' && (
            <div className="flex flex-col h-full">
              <div className="p-3 border-b border-slate-800">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">OSINT Transform Hub</h3>
                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
                  <input
                    type="text"
                    className="input pl-8 py-1 text-xs"
                    placeholder="Search transforms..."
                    value={transformFilter}
                    onChange={(e) => setTransformFilter(e.target.value)}
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2 space-y-2">
                {transforms
                  .filter((t) => t.name.toLowerCase().includes(transformFilter.toLowerCase()) || t.category.toLowerCase().includes(transformFilter.toLowerCase()))
                  .map((t) => (
                    <div key={t.id} className="p-2.5 rounded bg-slate-950 border border-slate-800 hover:border-slate-700 space-y-1 group">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-blue-400">{t.category}</span>
                        <span className="badge bg-emerald-500/10 text-emerald-400">READY</span>
                      </div>
                      <h4 className="text-xs font-semibold text-white group-hover:text-blue-300">{t.name}</h4>
                      <p className="text-[11px] text-slate-400 line-clamp-2">{t.desc}</p>
                    </div>
                  ))}
              </div>
            </div>
          )}

          {activeTab === 'evidence' && (
            <div className="p-3 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Evidence Locker</h3>
                <button className="btn btn-secondary text-xs h-7 px-2">
                  <Plus className="w-3 h-3" /> Log Item
                </button>
              </div>
              <div className="p-3 rounded bg-slate-950 border border-slate-800 text-center text-xs text-slate-500">
                No evidence items attached to this investigation yet.
              </div>
            </div>
          )}

          {activeTab === 'saved_queries' && (
            <div className="p-3 space-y-3">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider border-b border-slate-800 pb-2">Saved Graph Queries</h3>
              <div className="space-y-1.5 text-xs">
                <div className="p-2 rounded bg-slate-950 border border-slate-800 hover:border-blue-500/50 cursor-pointer">
                  <p className="font-semibold text-slate-200">High Risk Subdomains</p>
                  <p className="text-[10px] text-slate-500 font-mono">entity_type:subdomain AND confidence &lt; 0.8</p>
                </div>
                <div className="p-2 rounded bg-slate-950 border border-slate-800 hover:border-blue-500/50 cursor-pointer">
                  <p className="font-semibold text-slate-200">Open Port Vulnerabilities</p>
                  <p className="text-[10px] text-slate-500 font-mono">relationship_type:open_port</p>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'reports' && (
            <div className="p-4 text-slate-400 text-sm">Case Files & Reports coming soon.</div>
          )}
          </>
        )}
      </div>
    </div>
  );
}
