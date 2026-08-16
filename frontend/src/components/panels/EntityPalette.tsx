import { useState } from 'react';
import {
  Globe, Mail, Phone, User, Building2, Link, Server, Shield, Code,
  Hash, Bug, AlertTriangle, Flag, MapPin, Wallet, AtSign, Image,
  FileText, Video, Music, Share2, Search, Plus, Puzzle, Network, Lock,
} from 'lucide-react';

interface EntityPaletteProps {
  onSelectType: (type: string) => void;
}

const CATEGORIZED_ENTITIES = [
  {
    category: 'Infrastructure & Web',
    items: [
      { type: 'domain', label: 'Domain', icon: Globe, color: '#10B981' },
      { type: 'subdomain', label: 'Subdomain', icon: Globe, color: '#34D399' },
      { type: 'ip_address', label: 'IP Address', icon: Server, color: '#F59E0B' },
      { type: 'url', label: 'URL', icon: Link, color: '#06B6D4' },
      { type: 'server', label: 'Server', icon: Server, color: '#64748B' },
      { type: 'certificate', label: 'SSL Cert', icon: Lock, color: '#22C55E' },
    ],
  },
  {
    category: 'Identity & Social',
    items: [
      { type: 'person', label: 'Person', icon: User, color: '#3B82F6' },
      { type: 'organization', label: 'Organization', icon: Building2, color: '#8B5CF6' },
      { type: 'email', label: 'Email Address', icon: Mail, color: '#EC4899' },
      { type: 'phone', label: 'Phone Number', icon: Phone, color: '#14B8A6' },
      { type: 'username', label: 'Username', icon: AtSign, color: '#8B5CF6' },
      { type: 'social_profile', label: 'Social Profile', icon: Share2, color: '#E11D48' },
    ],
  },
  {
    category: 'Security & Threat Intel',
    items: [
      { type: 'cve', label: 'CVE Vulnerability', icon: Shield, color: '#DC2626' },
      { type: 'malware', label: 'Malware Sample', icon: Bug, color: '#EF4444' },
      { type: 'threat_actor', label: 'Threat Actor', icon: Shield, color: '#7C3AED' },
      { type: 'ioc', label: 'IOC Indicator', icon: AlertTriangle, color: '#F97316' },
      { type: 'hash', label: 'File Hash', icon: Hash, color: '#71717A' },
    ],
  },
  {
    category: 'Crypto & Assets',
    items: [
      { type: 'wallet', label: 'Crypto Wallet', icon: Wallet, color: '#F7931A' },
      { type: 'bitcoin_wallet', label: 'Bitcoin Wallet', icon: Wallet, color: '#F7931A' },
      { type: 'ethereum_wallet', label: 'ETH Wallet', icon: Wallet, color: '#627EEA' },
    ],
  },
];

export default function EntityPalette({ onSelectType }: EntityPaletteProps) {
  const [filter, setFilter] = useState('');

  return (
    <div className="flex flex-col h-full bg-slate-900 border-r border-slate-800 w-64 select-none">
      <div className="p-3 border-b border-slate-800">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2">Entity Palette</h3>
        <div className="relative">
          <Search className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            className="input pl-8 py-1 text-xs"
            placeholder="Filter entities..."
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        {CATEGORIZED_ENTITIES.map((cat) => {
          const filteredItems = cat.items.filter(
            (item) => item.label.toLowerCase().includes(filter.toLowerCase()) || item.type.includes(filter.toLowerCase()),
          );

          if (filteredItems.length === 0) return null;

          return (
            <div key={cat.category}>
              <h4 className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">{cat.category}</h4>
              <div className="grid grid-cols-2 gap-1.5">
                {filteredItems.map((item) => {
                  const IconComp = item.icon;
                  return (
                    <button
                      key={item.type}
                      onClick={() => onSelectType(item.type)}
                      className="flex items-center gap-2 p-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/50 hover:border-blue-500/50 text-left transition-all group"
                    >
                      <div
                        className="w-6 h-6 rounded flex items-center justify-center shrink-0"
                        style={{ background: `${item.color}20`, color: item.color }}
                      >
                        <IconComp className="w-3.5 h-3.5" />
                      </div>
                      <span className="text-[11px] font-medium text-slate-200 group-hover:text-white truncate">
                        {item.label}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
