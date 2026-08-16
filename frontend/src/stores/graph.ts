import { create } from 'zustand';
import type { Node, Edge } from '@xyflow/react';

interface GraphState {
  nodes: Node[];
  edges: Edge[];
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  undoStack: Array<{ nodes: Node[]; edges: Edge[] }>;
  redoStack: Array<{ nodes: Node[]; edges: Edge[] }>;

  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  addNode: (node: Node) => void;
  addEdge: (edge: Edge) => void;
  removeNode: (nodeId: string) => void;
  removeEdge: (edgeId: string) => void;
  updateNodePosition: (nodeId: string, x: number, y: number) => void;
  setSelectedNodes: (ids: string[]) => void;
  setSelectedEdges: (ids: string[]) => void;
  clearSelection: () => void;

  pushUndo: () => void;
  undo: () => void;
  redo: () => void;
  clearGraph: () => void;
}

export const useGraphStore = create<GraphState>()((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeIds: [],
  selectedEdgeIds: [],
  undoStack: [],
  redoStack: [],

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  addNode: (node) => {
    const state = get();
    state.pushUndo();
    set({ nodes: [...state.nodes, node], redoStack: [] });
  },

  addEdge: (edge) => {
    const state = get();
    state.pushUndo();
    set({ edges: [...state.edges, edge], redoStack: [] });
  },

  removeNode: (nodeId) => {
    const state = get();
    state.pushUndo();
    set({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
      edges: state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      redoStack: [],
    });
  },

  removeEdge: (edgeId) => {
    const state = get();
    state.pushUndo();
    set({
      edges: state.edges.filter((e) => e.id !== edgeId),
      redoStack: [],
    });
  },

  updateNodePosition: (nodeId, x, y) => {
    set((state) => ({
      nodes: state.nodes.map((n) =>
        n.id === nodeId ? { ...n, position: { x, y } } : n,
      ),
    }));
  },

  setSelectedNodes: (ids) => set({ selectedNodeIds: ids }),
  setSelectedEdges: (ids) => set({ selectedEdgeIds: ids }),
  clearSelection: () => set({ selectedNodeIds: [], selectedEdgeIds: [] }),

  pushUndo: () => {
    const { nodes, edges, undoStack } = get();
    const snapshot = { nodes: [...nodes], edges: [...edges] };
    const newStack = [...undoStack, snapshot].slice(-50);
    set({ undoStack: newStack });
  },

  undo: () => {
    const { nodes, edges, undoStack, redoStack } = get();
    if (undoStack.length === 0) return;

    const previous = undoStack[undoStack.length - 1];
    const newUndoStack = undoStack.slice(0, -1);

    set({
      nodes: previous.nodes,
      edges: previous.edges,
      undoStack: newUndoStack,
      redoStack: [...redoStack, { nodes: [...nodes], edges: [...edges] }],
    });
  },

  redo: () => {
    const { nodes, edges, undoStack, redoStack } = get();
    if (redoStack.length === 0) return;

    const next = redoStack[redoStack.length - 1];
    const newRedoStack = redoStack.slice(0, -1);

    set({
      nodes: next.nodes,
      edges: next.edges,
      undoStack: [...undoStack, { nodes: [...nodes], edges: [...edges] }],
      redoStack: newRedoStack,
    });
  },

  clearGraph: () => {
    const state = get();
    state.pushUndo();
    set({ nodes: [], edges: [], redoStack: [] });
  },
}));
