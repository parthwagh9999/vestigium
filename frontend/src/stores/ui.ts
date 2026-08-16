import { create } from 'zustand';

interface UIState {
  sidebarOpen: boolean;
  sidebarTab: 'entities' | 'properties' | 'transforms' | 'evidence' | 'notes';
  rightPanelOpen: boolean;
  rightPanelTab: 'details' | 'history' | 'timeline' | 'transforms';
  searchOpen: boolean;
  commandPaletteOpen: boolean;
  theme: 'dark' | 'light';
  canvasZoom: number;

  toggleSidebar: () => void;
  setSidebarTab: (tab: UIState['sidebarTab']) => void;
  toggleRightPanel: () => void;
  setRightPanelTab: (tab: UIState['rightPanelTab']) => void;
  toggleSearch: () => void;
  toggleCommandPalette: () => void;
  setCanvasZoom: (zoom: number) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  sidebarTab: 'entities',
  rightPanelOpen: false,
  rightPanelTab: 'details',
  searchOpen: false,
  commandPaletteOpen: false,
  theme: 'dark',
  canvasZoom: 1,

  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setSidebarTab: (tab) => set({ sidebarTab: tab, sidebarOpen: true }),
  toggleRightPanel: () => set((s) => ({ rightPanelOpen: !s.rightPanelOpen })),
  setRightPanelTab: (tab) => set({ rightPanelTab: tab, rightPanelOpen: true }),
  toggleSearch: () => set((s) => ({ searchOpen: !s.searchOpen })),
  toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  setCanvasZoom: (zoom) => set({ canvasZoom: zoom }),
}));
