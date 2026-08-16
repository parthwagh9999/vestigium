import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/stores/auth';
import apiClient, { type PaginatedResponse } from '@/api/client';
import {
  Shield,
  Plus,
  Search,
  FolderOpen,
  LayoutGrid,
  LogOut,
  Settings,
  Activity,
  Globe,
  Clock,
  MoreVertical,
  Briefcase,
  ChevronRight,
  Trash2,
} from 'lucide-react';
import logoUrl from '@/assets/logo.png';

interface WorkspaceItem {
  id: string;
  name: string;
  description: string | null;
  color: string | null;
  icon: string | null;
}

interface InvestigationItem {
  id: string;
  name: string;
  description: string | null;
  status: string;
  priority: string;
  entity_count: number;
  relationship_count: number;
  created_at: string;
  updated_at: string;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { user, logout } = useAuthStore();
  const [workspaces, setWorkspaces] = useState<WorkspaceItem[]>([]);
  const [investigations, setInvestigations] = useState<InvestigationItem[]>([]);
  const [activeWorkspace, setActiveWorkspace] = useState<string | null>(null);
  const [showNewInvestigation, setShowNewInvestigation] = useState(false);
  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [newName, setNewName] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [wsRes, invRes] = await Promise.all([
        apiClient.get<PaginatedResponse<WorkspaceItem>>('/workspaces'),
        apiClient.get<PaginatedResponse<InvestigationItem>>('/investigations'),
      ]);
      setWorkspaces(wsRes.data.items);
      setInvestigations(invRes.data.items);

      if (wsRes.data.items.length === 0) {
        const { data } = await apiClient.post('/workspaces', {
          name: 'Default Workspace',
          description: 'Your first workspace',
          color: '#3b82f6',
        });
        setWorkspaces([{ id: data.id, name: 'Default Workspace', description: 'Your first workspace', color: '#3b82f6', icon: null }]);
        setActiveWorkspace(data.id);
      } else {
        setActiveWorkspace(wsRes.data.items[0].id);
      }
    } catch (err) {
      console.error('Failed to load data:', err);
    } finally {
      setLoading(false);
    }
  };

  const createInvestigation = async () => {
    if (!newName.trim() || !activeWorkspace) return;
    try {
      const { data } = await apiClient.post('/investigations', {
        name: newName,
        workspace_id: activeWorkspace,
      });
      navigate(`/investigation/${data.id}`);
    } catch (err) {
      console.error('Failed to create investigation:', err);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const statusColors: Record<string, string> = {
    active: '#10b981',
    draft: '#6b7280',
    completed: '#3b82f6',
    paused: '#f59e0b',
    archived: '#64748b',
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: 'var(--color-vestigium-bg)' }}>
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-2 border-blue-500 border-t-transparent rounded-full" style={{ animation: 'spin-slow 1s linear infinite' }} />
          <p style={{ color: 'var(--color-vestigium-text-dim)' }}>Loading workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex" style={{ background: 'var(--color-vestigium-bg)' }}>
      {/* Sidebar */}
      <aside className="w-64 flex flex-col border-r" style={{ background: 'var(--color-vestigium-surface)', borderColor: 'var(--color-vestigium-border)' }}>
        {/* Logo */}
        <div className="p-4 flex items-center gap-3 border-b" style={{ borderColor: 'var(--color-vestigium-border)' }}>
          <div className="w-9 h-9 rounded-lg flex items-center justify-center">
            <img src={logoUrl} alt="VESTIGIUM Logo" className="w-full h-full object-contain" />
          </div>
          <div>
            <h1 className="text-sm font-bold text-white">VESTIGIUM</h1>
            <p className="text-[10px]" style={{ color: 'var(--color-vestigium-text-muted)' }}>v1.1</p>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-1">
          <button onClick={() => navigate('/')} className="btn btn-ghost w-full justify-start gap-3 text-sm h-9" style={{ color: 'var(--color-vestigium-accent)' }}>
            <LayoutGrid className="w-4 h-4" /> Dashboard
          </button>
          <button onClick={() => navigate('/')} className="btn btn-ghost w-full justify-start gap-3 text-sm h-9">
            <FolderOpen className="w-4 h-4" /> Investigations
          </button>
          <button onClick={() => navigate('/tools')} className="btn btn-ghost w-full justify-start gap-3 text-sm h-9">
            <Globe className="w-4 h-4" /> Transforms
          </button>
          <button onClick={() => alert('Activity feed coming soon')} className="btn btn-ghost w-full justify-start gap-3 text-sm h-9">
            <Activity className="w-4 h-4" /> Activity
          </button>
          <button onClick={() => alert('Global settings are managed in your `.agents` configuration.')} className="btn btn-ghost w-full justify-start gap-3 text-sm h-9">
            <Settings className="w-4 h-4" /> Settings
          </button>
        </nav>

        {/* User */}
        <div className="p-3 border-t" style={{ borderColor: 'var(--color-vestigium-border)' }}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-xs font-bold text-white">
              {user?.username?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{user?.username}</p>
              <p className="text-[10px] truncate" style={{ color: 'var(--color-vestigium-text-muted)' }}>{user?.email}</p>
            </div>
            <button onClick={handleLogout} className="btn btn-ghost p-1.5" title="Sign out">
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto">
        <div className="gradient-mesh min-h-full">
          {/* Header */}
          <div className="p-6 pb-0">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">Investigations</h2>
                <p className="text-sm mt-1" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                  {investigations.length} investigation{investigations.length !== 1 ? 's' : ''}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="relative">
                  <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2" style={{ color: 'var(--color-vestigium-text-muted)' }} />
                  <input className="input pl-9 w-64" placeholder="Search investigations..." />
                </div>
                <button
                  onClick={() => setShowNewInvestigation(true)}
                  className="btn btn-primary"
                >
                  <Plus className="w-4 h-4" /> New Investigation
                </button>
              </div>
            </div>
          </div>

          {/* Investigation Grid */}
          <div className="p-6 pt-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {investigations.map((inv) => (
              <div
                key={inv.id}
                className="glass p-5 text-left hover:glow-border transition-all duration-200 group relative flex flex-col"
              >
                <div className="flex items-start justify-between mb-3">
                  <h3 
                    className="text-base font-semibold text-white group-hover:text-blue-400 transition-colors cursor-pointer"
                    onClick={() => navigate(`/investigation/${inv.id}`)}
                  >
                    {inv.name}
                  </h3>
                  <div className="flex items-center gap-2">
                    <span
                      className="badge"
                      style={{
                        background: `${statusColors[inv.status] || '#6b7280'}20`,
                        color: statusColors[inv.status] || '#6b7280',
                      }}
                    >
                      {inv.status}
                    </span>
                    <button 
                      onClick={(e) => {
                        e.stopPropagation();
                        setDeleteConfirmId(inv.id);
                      }}
                      className="p-1.5 rounded-md hover:bg-red-500/20 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all"
                      title="Delete Investigation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
                {inv.description && (
                  <p className="text-sm mb-3 line-clamp-2" style={{ color: 'var(--color-vestigium-text-dim)' }}>
                    {inv.description}
                  </p>
                )}
                <div className="flex items-center gap-4 text-xs mt-auto" style={{ color: 'var(--color-vestigium-text-muted)' }}>
                  <span>{inv.entity_count} entities</span>
                  <span>{inv.relationship_count} relationships</span>
                  <span className="flex items-center gap-1 ml-auto">
                    <Clock className="w-3 h-3" />
                    {new Date(inv.updated_at).toLocaleDateString()}
                  </span>
                </div>
                <div 
                  className="mt-4 flex items-center gap-1 text-xs cursor-pointer w-fit" 
                  style={{ color: 'var(--color-vestigium-accent)' }}
                  onClick={() => navigate(`/investigation/${inv.id}`)}
                >
                  <span className="hover:underline">Open investigation</span>
                  <ChevronRight className="w-3 h-3" />
                </div>
              </div>
            ))}

            {/* Empty state */}
            {investigations.length === 0 && (
              <div className="col-span-full flex flex-col items-center justify-center py-20">
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500/10 to-purple-500/10 flex items-center justify-center mb-4 border" style={{ borderColor: 'var(--color-vestigium-border)' }}>
                  <FolderOpen className="w-8 h-8" style={{ color: 'var(--color-vestigium-text-muted)' }} />
                </div>
                <p className="text-lg font-medium text-white mb-1">No investigations yet</p>
                <p className="text-sm mb-6" style={{ color: 'var(--color-vestigium-text-dim)' }}>Create your first investigation to get started</p>
                <button onClick={() => setShowNewInvestigation(true)} className="btn btn-primary">
                  <Plus className="w-4 h-4" /> Create Investigation
                </button>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* New Investigation Modal */}
      {showNewInvestigation && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.6)' }}>
          <div className="glass p-6 w-full max-w-md animate-fade-in">
            <h3 className="text-lg font-bold text-white mb-4">New Investigation</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1.5" style={{ color: 'var(--color-vestigium-text-dim)' }}>Name</label>
                <input
                  className="input"
                  placeholder="e.g., Domain Infrastructure Analysis"
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && createInvestigation()}
                />
              </div>
              <div className="flex justify-end gap-3">
                <button onClick={() => setShowNewInvestigation(false)} className="btn btn-secondary">Cancel</button>
                <button onClick={createInvestigation} className="btn btn-primary">Create</button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteConfirmId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)' }}>
          <div className="glass p-6 w-full max-w-md animate-fade-in">
            <h3 className="text-lg font-bold text-white mb-2">Delete Investigation</h3>
            <p className="text-sm mb-6" style={{ color: 'var(--color-vestigium-text-dim)' }}>
              Are you sure you want to delete this investigation and all its generated entities? This action cannot be undone.
            </p>
            <div className="flex justify-end gap-3">
              <button onClick={() => setDeleteConfirmId(null)} className="btn btn-secondary" disabled={isDeleting}>Cancel</button>
              <button 
                onClick={async () => {
                  setIsDeleting(true);
                  try {
                    await apiClient.delete(`/investigations/${deleteConfirmId}`);
                    setInvestigations(prev => prev.filter(i => i.id !== deleteConfirmId));
                  } catch (err) {
                    console.error('Failed to delete investigation:', err);
                  } finally {
                    setIsDeleting(false);
                    setDeleteConfirmId(null);
                  }
                }} 
                className="btn bg-red-600 hover:bg-red-500 text-white"
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
