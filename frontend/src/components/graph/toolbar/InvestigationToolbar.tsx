import { Plus, Search, Filter, Download, Upload, BarChart3 } from 'lucide-react';

interface InvestigationToolbarProps {
  onAddEntity: () => void;
  onSearch: () => void;
  onExport?: () => void;
  onImport?: () => void;
  onStats?: () => void;
}

export default function InvestigationToolbar({
  onAddEntity,
  onSearch,
  onExport,
  onImport,
  onStats,
}: InvestigationToolbarProps) {
  return (
    <div
      className="glass-subtle flex items-center gap-1 p-1.5"
      style={{ borderRadius: '10px' }}
    >
      <button
        onClick={onAddEntity}
        className="btn btn-ghost p-2"
        title="Add Entity"
      >
        <Plus className="w-4 h-4" />
      </button>
      <button
        onClick={onSearch}
        className="btn btn-ghost p-2"
        title="Search (Ctrl+F)"
      >
        <Search className="w-4 h-4" />
      </button>
      <div className="w-px h-5" style={{ background: 'var(--color-vestigium-border)' }} />
      {onImport && (
        <button onClick={onImport} className="btn btn-ghost p-2" title="Import Data">
          <Upload className="w-4 h-4" />
        </button>
      )}
      {onExport && (
        <button onClick={onExport} className="btn btn-ghost p-2" title="Export Graph">
          <Download className="w-4 h-4" />
        </button>
      )}
      {onStats && (
        <button onClick={onStats} className="btn btn-ghost p-2" title="Graph Statistics">
          <BarChart3 className="w-4 h-4" />
        </button>
      )}
    </div>
  );
}
