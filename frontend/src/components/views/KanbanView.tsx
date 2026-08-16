import { useState } from 'react';
import { CheckSquare, Plus, Clock, User, AlertCircle, CheckCircle2 } from 'lucide-react';

interface TaskItem {
  id: string;
  title: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'todo' | 'in_progress' | 'verified' | 'closed';
  assignee: string;
}

export default function KanbanView() {
  const [tasks, setTasks] = useState<TaskItem[]>([
    { id: '1', title: 'Verify WHOIS Registrant Email Ownership', category: 'Attribution', priority: 'high', status: 'in_progress', assignee: 'admin' },
    { id: '2', title: 'Run Shodan Port Scan on Target IPs', category: 'Infrastructure', priority: 'critical', status: 'todo', assignee: 'admin' },
    { id: '3', title: 'Cross-reference Subdomains with CT Logs', category: 'Reconnaissance', priority: 'medium', status: 'verified', assignee: 'admin' },
    { id: '4', title: 'Export Investigation Graph snapshot to PDF', category: 'Reporting', priority: 'low', status: 'closed', assignee: 'admin' },
  ]);

  const columns = [
    { id: 'todo', label: 'To Do', color: '#64748B' },
    { id: 'in_progress', label: 'In Progress', color: '#3B82F6' },
    { id: 'verified', label: 'Verified Evidence', color: '#8B5CF6' },
    { id: 'closed', label: 'Closed & Resolved', color: '#10B981' },
  ] as const;

  return (
    <div className="flex-1 flex flex-col bg-slate-950 overflow-hidden p-4 select-none">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <CheckSquare className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-bold text-white uppercase tracking-wider">Case Management Task Board</h2>
        </div>
        <button className="btn btn-primary text-xs h-8 px-3">
          <Plus className="w-3.5 h-3.5" /> Create Task
        </button>
      </div>

      <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-3 overflow-y-auto">
        {columns.map((col) => {
          const colTasks = tasks.filter((t) => t.status === col.id);
          return (
            <div key={col.id} className="bg-slate-900 border border-slate-800 rounded p-3 flex flex-col h-full">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2 mb-3">
                <span className="text-xs font-bold uppercase tracking-wider text-white flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ background: col.color }} />
                  {col.label}
                </span>
                <span className="badge bg-slate-800 text-slate-400">{colTasks.length}</span>
              </div>

              <div className="flex-1 space-y-2.5 overflow-y-auto">
                {colTasks.map((t) => (
                  <div key={t.id} className="p-3 rounded bg-slate-950 border border-slate-800 hover:border-slate-700 space-y-2 cursor-pointer group">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">{t.category}</span>
                      <span className={`badge ${t.priority === 'critical' ? 'bg-red-500/20 text-red-400' : 'bg-blue-500/20 text-blue-400'}`}>
                        {t.priority}
                      </span>
                    </div>
                    <h4 className="text-xs font-semibold text-white group-hover:text-blue-300">{t.title}</h4>
                    <div className="flex items-center justify-between text-[10px] text-slate-500 border-t border-slate-800/80 pt-2 font-mono">
                      <span className="flex items-center gap-1"><User className="w-3 h-3" /> {t.assignee}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
