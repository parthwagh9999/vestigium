import { useEffect, useState, useMemo } from 'react';
import {
  Settings,
  Shield,
  Globe,
  Wrench,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Search,
  Play,
  ExternalLink,
  Layers,
  Zap,
  Lock,
  Cpu,
  Clock,
  ArrowRight,
  X,
} from 'lucide-react';
import apiClient from '@/api/client';
import TransformRunnerModal from '@/components/panels/TransformRunnerModal';

interface ToolParam {
  name: string;
  display_name: string;
  param_type: string;
  required: boolean;
}

interface OSINTTool {
  id: string;
  name: string;
  description: string;
  category: string;
  author: string;
  version: string;
  source: string;
  documentation_url: string | null;
  license: string;
  is_passive: boolean;
  passive_or_active: string;
  execution_type: string;
  authorization_required: boolean;
  requires_api_key: boolean;
  api_key_required: boolean;
  installation_required: boolean;
  install_status: 'installed' | 'not_installed' | 'error';
  availability_status: string;
  installed_version: string | null;
  configuration_status: string;
  rate_limit: string | null;
  timeout: number;
  supports_recursive_investigation: boolean;
  supported_os: string[];
  params: ToolParam[];
  input_entity_types: string[];
  output_entity_types: string[];
  relationships_created: string[];
}

interface ToolStats {
  total: number;
  available: number;
  api_required: number;
  installation_required: number;
  not_installed: number;
  passive: number;
  active_authorized: number;
  categories: string[];
}

export default function ToolCenter() {
  const [tools, setTools] = useState<OSINTTool[]>([]);
  const [stats, setStats] = useState<ToolStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedFilter, setSelectedFilter] = useState<string>('all');
  const [selectedTool, setSelectedTool] = useState<OSINTTool | null>(null);

  // Runner State
  const [showRunner, setShowRunner] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [toolsRes, statsRes] = await Promise.all([
        apiClient.get<OSINTTool[]>('/tools'),
        apiClient.get<ToolStats>('/tools/stats'),
      ]);
      setTools(toolsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to fetch tools or stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRunTransform = async (targetValue: string, targetType: string, params: Record<string, string>) => {
    // In a real implementation this would queue the job and navigate to investigation/jobs
    // For now we just close the modal
    setShowRunner(false);
    console.log(`Running ${selectedTool?.id} against ${targetValue} (${targetType}) with params`, params);
  };

  const categories = useMemo(() => {
    const cats = new Set(tools.map((t) => t.category));
    return ['All', ...Array.from(cats).sort()];
  }, [tools]);

  const filteredTools = useMemo(() => {
    return tools.filter((tool) => {
      // Category match
      if (selectedCategory !== 'All' && tool.category !== selectedCategory) {
        return false;
      }

      // Filter pills
      if (selectedFilter === 'available' && !tool.availability_status.startsWith('AVAILABLE')) {
        return false;
      }
      if (selectedFilter === 'passive' && tool.passive_or_active !== 'PASSIVE' && !tool.is_passive) {
        return false;
      }
      if (selectedFilter === 'active' && tool.passive_or_active !== 'ACTIVE_AUTHORIZED') {
        return false;
      }
      if (selectedFilter === 'api_required' && !tool.api_key_required && !tool.requires_api_key) {
        return false;
      }
      if (selectedFilter === 'binary' && tool.execution_type !== 'binary' && !tool.installation_required) {
        return false;
      }

      // Search
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        const matchesName = tool.name.toLowerCase().includes(q);
        const matchesDesc = tool.description.toLowerCase().includes(q);
        const matchesCat = tool.category.toLowerCase().includes(q);
        const matchesInputs = tool.input_entity_types.some((t) => t.toLowerCase().includes(q));
        const matchesOutputs = tool.output_entity_types.some((t) => t.toLowerCase().includes(q));
        return matchesName || matchesDesc || matchesCat || matchesInputs || matchesOutputs;
      }

      return true;
    });
  }, [tools, selectedCategory, selectedFilter, searchQuery]);

  if (loading && tools.length === 0) {
    return (
      <div className="flex-1 flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-4 text-slate-400">
          <div className="w-10 h-10 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm font-mono tracking-wider">Loading OSINT Tool Ecosystem...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full bg-slate-950 text-slate-100 overflow-hidden select-none">
      {/* Top Header */}
      <header className="h-16 border-b border-slate-800/80 bg-slate-900/60 backdrop-blur-xl flex items-center justify-between px-6 shrink-0 z-20">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500/20 to-purple-600/20 border border-blue-500/30 flex items-center justify-center shadow-lg shadow-blue-500/10">
            <Wrench className="w-5 h-5 text-blue-400" />
          </div>
          <div>
            <h1 className="text-base font-bold text-white flex items-center gap-2 tracking-wide">
              OSINT Tool Center
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-blue-500/10 border border-blue-500/30 text-blue-400">
                v2.0 Professional
              </span>
            </h1>
            <p className="text-xs text-slate-400">
              Orchestrating {tools.length} defensive OSINT modules across {categories.length - 1} domains
            </p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            className="btn btn-secondary text-xs h-9 px-3 gap-2 border-slate-700 bg-slate-800/50 hover:bg-slate-800"
            onClick={() => fetchData()}
          >
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            Probe Health
          </button>
        </div>
      </header>

      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3 p-6 pb-2 shrink-0 bg-slate-950/40">
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
              <Layers className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">Total Tools</p>
              <p className="text-lg font-bold text-white">{stats.total}</p>
            </div>
          </div>
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <CheckCircle className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">Available</p>
              <p className="text-lg font-bold text-emerald-400">{stats.available}</p>
            </div>
          </div>
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-400">
              <Zap className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">Passive Auto</p>
              <p className="text-lg font-bold text-purple-300">{stats.passive}</p>
            </div>
          </div>
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-red-500/10 text-red-400">
              <Shield className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">Active (Auth)</p>
              <p className="text-lg font-bold text-red-400">{stats.active_authorized}</p>
            </div>
          </div>
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
              <Lock className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">API Keys</p>
              <p className="text-lg font-bold text-amber-400">{stats.api_required}</p>
            </div>
          </div>
          <div className="glass p-3 rounded-xl border border-slate-800/80 flex items-center gap-3">
            <div className="p-2 rounded-lg bg-slate-500/10 text-slate-400">
              <Cpu className="w-4 h-4" />
            </div>
            <div>
              <p className="text-[10px] text-slate-400 uppercase font-mono">CLI Binaries</p>
              <p className="text-lg font-bold text-slate-300">{stats.installation_required}</p>
            </div>
          </div>
        </div>
      )}

      {/* Filter & Category Controls */}
      <div className="px-6 py-3 border-b border-slate-800/80 flex flex-col gap-3 shrink-0 bg-slate-900/30">
        {/* Search & Filter pills */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              placeholder="Search by tool name, capability, input or output..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-500 hover:text-white text-xs"
              >
                ×
              </button>
            )}
          </div>

          <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-1">
            {[
              { id: 'all', label: 'All Modules' },
              { id: 'available', label: 'Available' },
              { id: 'passive', label: 'Passive Only' },
              { id: 'active', label: 'Active Authorized' },
              { id: 'api_required', label: 'API Required' },
              { id: 'binary', label: 'CLI Binary' },
            ].map((f) => (
              <button
                key={f.id}
                onClick={() => setSelectedFilter(f.id)}
                className={`text-xs px-2.5 py-1 rounded-md font-medium transition-all ${
                  selectedFilter === f.id
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-500/20'
                    : 'bg-slate-800/60 text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>

        {/* Category Badges Bar */}
        <div className="flex items-center gap-1.5 overflow-x-auto custom-scrollbar pb-1">
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`text-[11px] px-3 py-1 rounded-full whitespace-nowrap border transition-all ${
                selectedCategory === cat
                  ? 'bg-blue-500/10 border-blue-500/40 text-blue-300 font-semibold'
                  : 'bg-slate-900/40 border-slate-800/80 text-slate-400 hover:border-slate-700 hover:text-slate-300'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Main Tools Grid */}
      <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-5">
          {filteredTools.map((tool, idx) => (
            <div
              key={tool.id}
              onClick={() => {
                setSelectedTool(tool);
              }}
              className={`glass rounded-xl border border-slate-800/80 overflow-hidden flex flex-col hover:border-blue-500/40 hover:shadow-[0_0_20px_rgba(59,130,246,0.15)] hover:-translate-y-1 transition-all duration-300 cursor-pointer group animate-cascade-in stagger-${(idx % 5) + 1}`}
            >
              <div className="p-4 border-b border-slate-800/60 bg-slate-900/40 flex flex-col gap-2">
                <div className="flex justify-between items-start">
                  <h3 className="font-semibold text-white group-hover:text-blue-400 transition-colors text-sm">
                    {tool.name}
                  </h3>
                  {tool.passive_or_active === 'PASSIVE' ? (
                    <span className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] px-2 py-0.5 rounded uppercase font-mono font-bold tracking-wider">
                      Passive
                    </span>
                  ) : tool.passive_or_active === 'ACTIVE_AUTHORIZED' ? (
                    <span className="bg-red-500/10 border border-red-500/20 text-red-400 text-[9px] px-2 py-0.5 rounded uppercase font-mono font-bold tracking-wider flex items-center gap-1">
                      <Shield className="w-2.5 h-2.5" /> Active
                    </span>
                  ) : (
                    <span className="bg-amber-500/10 border border-amber-500/20 text-amber-400 text-[9px] px-2 py-0.5 rounded uppercase font-mono font-bold tracking-wider">
                      Low Impact
                    </span>
                  )}
                </div>
                <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed" title={tool.description}>
                  {tool.description}
                </p>
                <div className="flex items-center gap-1.5 flex-wrap pt-1">
                  <span className="text-[10px] bg-slate-950 border border-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">
                    v{tool.version}
                  </span>
                  <span className="text-[10px] bg-slate-950 border border-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                    {tool.category}
                  </span>
                  <span className="text-[10px] bg-indigo-500/10 border border-indigo-500/30 text-indigo-400 px-1.5 py-0.5 rounded font-mono uppercase">
                    {tool.execution_type}
                  </span>
                </div>
              </div>

              <div className="p-4 flex-1 space-y-3 bg-slate-950/20 flex flex-col justify-between">
                {/* Status Indicator */}
                <div className="flex items-center justify-between text-xs pt-1">
                  <span className="text-slate-500 text-[11px]">Availability:</span>
                  {tool.availability_status.startsWith('AVAILABLE') ? (
                    <div className="flex items-center gap-1.5 text-emerald-400 text-xs font-medium">
                      <CheckCircle className="w-3.5 h-3.5" />
                      <span>Ready</span>
                    </div>
                  ) : tool.availability_status === 'NOT_INSTALLED' ? (
                    <div className="flex items-center gap-1.5 text-slate-500 text-xs">
                      <XCircle className="w-3.5 h-3.5" />
                      <span>Not Installed</span>
                    </div>
                  ) : tool.availability_status === 'AVAILABLE_WITH_API_KEY' ? (
                    <div className="flex items-center gap-1.5 text-amber-400 text-xs">
                      <Lock className="w-3.5 h-3.5" />
                      <span>API Key Needed</span>
                    </div>
                  ) : (
                    <div className="flex items-center gap-1.5 text-red-400 text-xs">
                      <AlertTriangle className="w-3.5 h-3.5" />
                      <span>{tool.availability_status.replace(/_/g, ' ')}</span>
                    </div>
                  )}
                </div>

                {/* Input / Output Tags */}
                <div className="space-y-2 pt-2 border-t border-slate-800/60">
                  <div>
                    <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-500 block mb-1">
                      Input Targets
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {tool.input_entity_types.map((t) => (
                        <span key={t} className="text-[10px] bg-slate-900 border border-slate-800 text-slate-300 px-1.5 py-0.5 rounded font-mono">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div>
                    <span className="text-[9px] font-mono font-bold uppercase tracking-wider text-slate-500 block mb-1">
                      Generated Graph Entities
                    </span>
                    <div className="flex flex-wrap gap-1">
                      {tool.output_entity_types.map((t) => (
                        <span key={t} className="text-[10px] bg-blue-500/10 border border-blue-500/20 text-blue-300 px-1.5 py-0.5 rounded font-mono">
                          {t}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Footer Link */}
                <div className="pt-2 flex items-center justify-between text-xs text-slate-500 border-t border-slate-800/40">
                  <span className="flex items-center gap-1 font-mono text-[10px]">
                    <Clock className="w-3 h-3" /> {tool.timeout}s timeout
                  </span>
                  <span className="text-blue-400 group-hover:translate-x-0.5 transition-transform flex items-center gap-1 text-[11px] font-medium">
                    Details <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            </div>
          ))}

          {filteredTools.length === 0 && (
            <div className="col-span-full py-16 flex flex-col items-center justify-center text-slate-500">
              <Search className="w-10 h-10 mb-3 opacity-30" />
              <p className="text-sm font-medium">No OSINT tools match your filter criteria</p>
              <button
                onClick={() => {
                  setSelectedCategory('All');
                  setSelectedFilter('all');
                  setSearchQuery('');
                }}
                className="mt-3 text-xs text-blue-400 hover:underline"
              >
                Clear all filters
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Tool Details Modal */}
      {selectedTool && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in">
          <div className="glass rounded-2xl border border-slate-700/80 bg-slate-900/95 w-full max-w-2xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl shadow-blue-500/10">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-start justify-between bg-slate-800/40">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/10 border border-blue-500/30 flex items-center justify-center text-blue-400">
                  <Wrench className="w-5 h-5" />
                </div>
                <div>
                  <h2 className="text-base font-bold text-white flex items-center gap-2">
                    {selectedTool.name}
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                      v{selectedTool.version}
                    </span>
                  </h2>
                  <p className="text-xs text-slate-400">{selectedTool.category} • {selectedTool.source}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedTool(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 overflow-y-auto custom-scrollbar space-y-5 flex-1">
              <div>
                <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 mb-1.5">Description</h4>
                <p className="text-sm text-slate-300 leading-relaxed bg-slate-950/50 p-3 rounded-lg border border-slate-800">
                  {selectedTool.description}
                </p>
              </div>

              {/* Execution Profile Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] font-mono uppercase">Execution</span>
                  <span className="font-semibold text-slate-200 capitalize">{selectedTool.execution_type}</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] font-mono uppercase">Posture</span>
                  <span className={`font-semibold ${selectedTool.passive_or_active === 'PASSIVE' ? 'text-emerald-400' : 'text-red-400'}`}>
                    {selectedTool.passive_or_active.replace(/_/g, ' ')}
                  </span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] font-mono uppercase">Timeout</span>
                  <span className="font-semibold text-slate-200">{selectedTool.timeout} seconds</span>
                </div>
                <div className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800">
                  <span className="text-slate-500 block text-[10px] font-mono uppercase">Auto Recursive</span>
                  <span className={`font-semibold ${selectedTool.supports_recursive_investigation ? 'text-emerald-400' : 'text-slate-500'}`}>
                    {selectedTool.supports_recursive_investigation ? 'Enabled (10 layers)' : 'Manual Only'}
                  </span>
                </div>
              </div>

              {/* Input & Output Matrices */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
                <div>
                  <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 mb-2">Supported Input Entities</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedTool.input_entity_types.map((t) => (
                      <span key={t} className="text-xs bg-slate-800 text-slate-200 px-2 py-1 rounded border border-slate-700 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs font-mono uppercase tracking-wider text-slate-500 mb-2">Discovered Output Entities</h4>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedTool.output_entity_types.map((t) => (
                      <span key={t} className="text-xs bg-blue-500/10 text-blue-300 px-2 py-1 rounded border border-blue-500/30 font-mono">
                        {t}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Documentation & License */}
              <div className="flex items-center justify-between pt-2 border-t border-slate-800 text-xs text-slate-400">
                <span>License: <strong className="text-slate-200">{selectedTool.license}</strong></span>
                {selectedTool.documentation_url && (
                  <a
                    href={selectedTool.documentation_url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center gap-1 text-blue-400 hover:underline"
                  >
                    Documentation <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>

            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 bg-slate-950/60 flex items-center justify-between">
              <button
                onClick={() => setSelectedTool(null)}
                className="btn btn-secondary text-xs px-4 h-9"
              >
                Close
              </button>
              <button
                onClick={() => setShowRunner(true)}
                className="btn btn-primary text-xs px-4 h-9 gap-2 shadow-lg shadow-blue-500/20"
              >
                <Play className="w-3.5 h-3.5" />
                Configure & Run
              </button>
            </div>
          </div>
        </div>
      )}
      {/* Transform Runner Modal */}
      {selectedTool && showRunner && (
        <TransformRunnerModal
          tool={selectedTool}
          isOpen={showRunner}
          onClose={() => setShowRunner(false)}
          onRun={handleRunTransform}
        />
      )}
    </div>
  );
}
