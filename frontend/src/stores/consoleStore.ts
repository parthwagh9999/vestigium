import { create } from 'zustand';

export interface LogEntry {
  time: string;
  level: 'INFO' | 'SUCCESS' | 'WARNING' | 'ERROR';
  message: string;
  details?: any;
}

export interface QueueItem {
  id: string;
  transformId: string;
  targetValue: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  durationSeconds?: number;
  entitiesCreated?: number;
  relationshipsCreated?: number;
  time: string;
}

export interface ApiLogEntry {
  id: string;
  method: string;
  url: string;
  status: number;
  statusText?: string;
  durationMs: number;
  time: string;
}

interface ConsoleState {
  logs: LogEntry[];
  queue: QueueItem[];
  apiLogs: ApiLogEntry[];
  addLog: (level: LogEntry['level'], message: string, details?: any) => void;
  addQueueItem: (item: Omit<QueueItem, 'time'> & { time?: string }) => void;
  updateQueueItem: (id: string, updates: Partial<QueueItem>) => void;
  addApiLog: (log: Omit<ApiLogEntry, 'id' | 'time'>) => void;
  clearLogs: () => void;
  clearQueue: () => void;
  clearApiLogs: () => void;
  clearAll: () => void;
}

export const useConsoleStore = create<ConsoleState>((set) => ({
  logs: [],
  queue: [],
  apiLogs: [],

  addLog: (level, message, details) =>
    set((state) => {
      const time = new Date().toLocaleTimeString('en-US', { hour12: false });
      const newLog = { time, level, message, details };
      return { logs: [...state.logs, newLog].slice(-500) };
    }),

  addQueueItem: (item) =>
    set((state) => {
      const time = item.time || new Date().toLocaleTimeString('en-US', { hour12: false });
      const existingIdx = state.queue.findIndex((q) => q.id === item.id);
      if (existingIdx >= 0) {
        const updated = [...state.queue];
        updated[existingIdx] = { ...updated[existingIdx], ...item, time };
        return { queue: updated };
      }
      return { queue: [item as QueueItem, ...state.queue].slice(0, 100) };
    }),

  updateQueueItem: (id, updates) =>
    set((state) => {
      const updated = state.queue.map((q) => (q.id === id ? { ...q, ...updates } : q));
      return { queue: updated };
    }),

  addApiLog: (log) =>
    set((state) => {
      const time = new Date().toLocaleTimeString('en-US', { hour12: false });
      const id = `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
      return { apiLogs: [{ ...log, id, time }, ...state.apiLogs].slice(0, 100) };
    }),

  clearLogs: () => set({ logs: [] }),
  clearQueue: () => set({ queue: [] }),
  clearApiLogs: () => set({ apiLogs: [] }),
  clearAll: () => set({ logs: [], queue: [], apiLogs: [] }),
}));
