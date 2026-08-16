import { create } from 'zustand';

export type LayoutMode = 'smart_force' | 'circular_layered' | 'clustered_circular' | 'galaxy_cluster' | 'intelligence_concept';

interface GraphState {
  selectedNodeId: string | null;
  selectedNodeIds: Set<string>; // For multi-selection
  selectedConnectedNodeIds: Set<string>;
  selectedConnectedEdgeIds: Set<string>;
  hoveredNodeId: string | null;
  highlightedNodeIds: Set<string>;
  highlightedEdgeIds: Set<string>;
  collapsedClusters: Set<string>;
  hiddenEntityTypes: Set<string>; // For visibility toggles
  
  // Layout Options
  layoutMode: LayoutMode;
  clusterThreshold: number;
  nodeSpacing: number;
  animationEnabled: boolean;

  setSelectedNode: (id: string | null, connectedNodeIds?: string[], connectedEdgeIds?: string[]) => void;
  setSelectedNodes: (ids: string[]) => void;
  setHoveredNode: (id: string | null, connectedNodeIds?: string[], connectedEdgeIds?: string[]) => void;
  clearHighlights: () => void;
  toggleCollapsedCluster: (clusterId: string) => void;
  toggleEntityTypeVisibility: (entityType: string, isVisible?: boolean) => void;
  hideAllEntityTypes: (allTypes: string[]) => void;
  showAllEntityTypes: () => void;
  setLayoutMode: (mode: LayoutMode) => void;
  setClusterThreshold: (threshold: number) => void;
  setNodeSpacing: (spacing: number) => void;
  setAnimationEnabled: (enabled: boolean) => void;
}

export const useGraphStore = create<GraphState>((set) => ({
  selectedNodeId: null,
  selectedNodeIds: new Set(),
  selectedConnectedNodeIds: new Set(),
  selectedConnectedEdgeIds: new Set(),
  hoveredNodeId: null,
  highlightedNodeIds: new Set(),
  highlightedEdgeIds: new Set(),
  collapsedClusters: new Set(),
  hiddenEntityTypes: new Set(),
  
  layoutMode: 'smart_force',
  clusterThreshold: 5,
  nodeSpacing: 1.0,
  animationEnabled: true,

  setSelectedNode: (id, connectedNodeIds = [], connectedEdgeIds = []) => {
    if (!id) {
      set({ selectedNodeId: null, selectedConnectedNodeIds: new Set(), selectedConnectedEdgeIds: new Set() });
      return;
    }
    const nodeIds = new Set(connectedNodeIds);
    nodeIds.add(id);
    set({
      selectedNodeId: id,
      selectedConnectedNodeIds: nodeIds,
      selectedConnectedEdgeIds: new Set(connectedEdgeIds)
    });
  },
  setSelectedNodes: (ids) => set({ selectedNodeIds: new Set(ids) }),
  
  setHoveredNode: (id, connectedNodeIds = [], connectedEdgeIds = []) => {
    if (!id) {
      set({ hoveredNodeId: null, highlightedNodeIds: new Set(), highlightedEdgeIds: new Set() });
      return;
    }
    const nodeIds = new Set(connectedNodeIds);
    nodeIds.add(id);
    set({
      hoveredNodeId: id,
      highlightedNodeIds: nodeIds,
      highlightedEdgeIds: new Set(connectedEdgeIds),
    });
  },

  clearHighlights: () => set({
    selectedNodeId: null,
    hoveredNodeId: null,
    highlightedNodeIds: new Set(),
    highlightedEdgeIds: new Set(),
  }),

  toggleCollapsedCluster: (clusterId) => set((state) => {
    const newCollapsed = new Set(state.collapsedClusters);
    if (newCollapsed.has(clusterId)) {
      newCollapsed.delete(clusterId);
    } else {
      newCollapsed.add(clusterId);
    }
    return { collapsedClusters: newCollapsed };
  }),

  toggleEntityTypeVisibility: (entityType, isVisible) => set((state) => {
    const newHidden = new Set(state.hiddenEntityTypes);
    const currentlyHidden = newHidden.has(entityType);
    
    // If isVisible is explicitly provided, respect it
    if (isVisible !== undefined) {
      if (isVisible) newHidden.delete(entityType);
      else newHidden.add(entityType);
    } else {
      // Otherwise toggle
      if (currentlyHidden) newHidden.delete(entityType);
      else newHidden.add(entityType);
    }
    return { hiddenEntityTypes: newHidden };
  }),

  hideAllEntityTypes: (allTypes) => set({ hiddenEntityTypes: new Set(allTypes) }),
  showAllEntityTypes: () => set({ hiddenEntityTypes: new Set() }),

  setLayoutMode: (mode) => set({ layoutMode: mode }),
  setClusterThreshold: (threshold) => set({ clusterThreshold: threshold }),
  setNodeSpacing: (spacing) => set({ nodeSpacing: spacing }),
  setAnimationEnabled: (enabled) => set({ animationEnabled: enabled }),
}));
