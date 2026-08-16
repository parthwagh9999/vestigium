import React, { useState } from 'react';
import { X } from 'lucide-react';

interface AddEntityModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (type: string, value: string) => void;
}

export default function AddEntityModal({ isOpen, onClose, onAdd }: AddEntityModalProps) {
  const [type, setType] = useState('domain');
  const [value, setValue] = useState('');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-[400px] overflow-hidden">
        <div className="flex items-center justify-between p-4 border-b border-slate-800">
          <h2 className="font-bold text-white">Add Entity</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-6 space-y-4">
          <div>
            <label className="block text-sm text-slate-300 mb-1">Type</label>
            <input type="text" value={type} onChange={e => setType(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-white" />
          </div>
          <div>
            <label className="block text-sm text-slate-300 mb-1">Value</label>
            <input type="text" value={value} onChange={e => setValue(e.target.value)} className="w-full bg-slate-800 border border-slate-700 rounded-md p-2 text-white" />
          </div>
        </div>
        <div className="p-4 border-t border-slate-800 flex justify-end gap-2">
          <button onClick={onClose} className="px-4 py-2 text-sm text-slate-300">Cancel</button>
          <button onClick={() => { onAdd(type, value); onClose(); }} className="px-4 py-2 text-sm bg-indigo-600 text-white rounded-md">Add</button>
        </div>
      </div>
    </div>
  );
}
