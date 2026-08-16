import { useState, useEffect, useRef } from 'react';
import {
  Search,
  Zap,
  Globe,
  Table,
  Clock,
  Grid,
  CheckSquare,
  Plus,
  Download,
  Layout,
  Maximize2,
  Trash2,
  SlidersHorizontal,
} from 'lucide-react';

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectCommand: (cmdId: string) => void;
  nodes?: { id: string; data?: { label?: string; value?: string; entityType?: string } }[];
}

export default function CommandPalette({ isOpen, onClose, onSelectCommand, nodes = [] }: CommandPaletteProps) {
  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && (e.key === 'k' || (e.shiftKey && e.key.toLowerCase() === 'p'))) {
        e.preventDefault();
        if (isOpen) onClose();
        else onSelectCommand('open_palette');
      }
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose, onSelectCommand]);

  if (!isOpen) return null;

  const commands = [
    { id: 'view_graph', title: 'Switch to Graph Canvas View', category: 'Navigation', icon: Globe },
    { id: 'view_table', title: 'Switch to Tabular Data View', category: 'Navigation', icon: Table },
    { id: 'view_timeline', title: 'Switch to Timeline View', category: 'Navigation', icon: Clock },
    { id: 'view_map', title: 'Switch to Map Geolocation View', category: 'Navigation', icon: Globe },
    { id: 'view_matrix', title: 'Switch to Relationship Matrix', category: 'Navigation', icon: Grid },
    { id: 'view_kanban', title: 'Switch to Case Tasks Kanban', category: 'Navigation', icon: CheckSquare },

    { id: 'transform_dns', title: 'Run DNS Lookup Transform', category: 'Transforms', icon: Zap },
    { id: 'transform_whois', title: 'Run WHOIS Query Transform', category: 'Transforms', icon: Zap },
    { id: 'transform_shodan', title: 'Run Shodan InternetDB Query', category: 'Transforms', icon: Zap },
    { id: 'transform_social', title: 'Run Social Media Account Search', category: 'Transforms', icon: Zap },

    { id: 'action_add_entity', title: 'Add Target Entity to Graph', category: 'Actions', icon: Plus },
    { id: 'action_auto_layout', title: 'Apply Graph Auto-Layout', category: 'Actions', icon: Layout },
    { id: 'action_fit_view', title: 'Fit Graph View to Screen', category: 'Actions', icon: Maximize2 },
    { id: 'action_export_json', title: 'Export Investigation as JSON', category: 'Export', icon: Download },
    { id: 'action_export_csv', title: 'Export Entities as CSV', category: 'Export', icon: Download },
    { id: 'action_export_graphml', title: 'Export Graph as GraphML', category: 'Export', icon: Download },
  ];

  // Map nodes to commands
  const nodeCommands = nodes.map(n => ({
    id: `node_${n.id}`,
    title: String(n.data?.label || n.data?.value || n.id),
    category: `Canvas Node (${n.data?.entityType || 'unknown'})`,
    icon: Globe,
  }));

  const allCommands = [...commands, ...nodeCommands];

  const filteredCommands = allCommands.filter(
    (c) => c.title.toLowerCase().includes(query.toLowerCase()) || c.category.toLowerCase().includes(query.toLowerCase()),
  ).slice(0, 50); // limit to 50 results to prevent UI lag

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-24 bg-slate-950/70 backdrop-blur-sm select-none">
      <div className="w-full max-w-xl bg-slate-900 border border-slate-800 rounded-lg shadow-2xl overflow-hidden animate-fade-in">
        {/* Input Bar */}
        <div className="flex items-center px-3 py-2 border-b border-slate-800">
          <Search className="w-4 h-4 text-slate-400 mr-2 shrink-0" />
          <input
            ref={inputRef}
            type="text"
            className="w-full bg-transparent text-white text-xs placeholder-slate-500 outline-none"
            placeholder="Type a command or search (e.g. 'DNS', 'Table', 'Export')..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <kbd className="text-[10px] bg-slate-800 border border-slate-700 px-1.5 py-0.5 rounded text-slate-400 font-mono">
            ESC
          </kbd>
        </div>

        {/* Command List */}
        <div className="max-h-80 overflow-y-auto p-1.5 space-y-1">
          {filteredCommands.length === 0 ? (
            <div className="p-4 text-center text-xs text-slate-500">No matching commands found.</div>
          ) : (
            filteredCommands.map((cmd) => {
              const Icon = cmd.icon;
              return (
                <button
                  key={cmd.id}
                  onClick={() => {
                    onSelectCommand(cmd.id);
                    onClose();
                  }}
                  className="w-full flex items-center justify-between p-2 rounded hover:bg-blue-600/20 text-left transition-colors group"
                >
                  <div className="flex items-center gap-2.5">
                    <div className="w-6 h-6 rounded bg-slate-800 group-hover:bg-blue-600/30 flex items-center justify-center text-slate-400 group-hover:text-blue-400">
                      <Icon className="w-3.5 h-3.5" />
                    </div>
                    <span className="text-xs font-medium text-slate-200 group-hover:text-white">{cmd.title}</span>
                  </div>
                  <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500 group-hover:text-blue-400 font-mono">
                    {cmd.category}
                  </span>
                </button>
              );
            })
          )}
        </div>
      </div>
    </div>
  );
}
