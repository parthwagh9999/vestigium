import { useCallback, useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Panel,
  useNodesState,
  useEdgesState,
  addEdge,
  type Connection,
  type Node,
  type Edge,
  BackgroundVariant,
  MarkerType,
  SelectionMode,
  useReactFlow,
  ReactFlowProvider,
  useOnSelectionChange,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import apiClient, { type PaginatedResponse } from '@/api/client';
import { useAuthStore } from '@/stores/auth';
import { useGraphStore, LayoutMode } from '@/stores/graphStore';
import { useUIStore } from '@/stores/ui';
import { useConsoleStore } from '@/stores/consoleStore';

import EntityNode, { COLOR_MAP } from '@/components/graph/nodes/EntityNode';
import SmartEdge from '@/components/graph/edges/SmartEdge';
import EntityPanel from '@/components/panels/EntityPanel';
import AddEntityModal from '@/components/panels/AddEntityModal';
import AutoInvestigateModal from '@/components/panels/AutoInvestigateModal';
import FilterPanel from '@/components/panels/FilterPanel';
import ContextMenu from '@/components/graph/ContextMenu';
import GraphToolbar from '@/components/graph/GraphToolbar';
import ClusterGroupNode from '@/components/graph/nodes/ClusterGroupNode';
import LayoutWorker from '@/workers/layout.worker?worker';

import AppHeader from '@/components/layout/AppHeader';
import LeftNavigationSidebar from '@/components/layout/LeftNavigationSidebar';
import BottomPanel from '@/components/layout/BottomPanel';
import CommandPalette from '@/components/layout/CommandPalette';

import TableView from '@/components/views/TableView';
import TimelineView from '@/components/views/TimelineView';
import MapView from '@/components/views/MapView';
import MatrixView from '@/components/views/MatrixView';
import KanbanView from '@/components/views/KanbanView';
import DashboardView from '@/components/views/DashboardView';

import {
  Save,
  Undo2,
  Redo2,
  Maximize2,
  Download,
  FileText,
  Layout,
  Plus,
  Target,
  Sparkles,
  PanelRightOpen,
  PanelRightClose,
  AlertTriangle,
  Filter,
  Trash2,
} from 'lucide-react';

const nodeTypes = {
  entity: EntityNode,
  cluster: ClusterGroupNode,
};

const edgeTypes = {
  smart: SmartEdge,
};

interface InvestigationData {
  id: string;
  name: string;
  description: string | null;
  status: string;
  root_entity_id: string | null;
}

interface EntityData {
  id: string;
  entity_type: string;
  label: string;
  value: string;
  confidence: number;
  source: string | null;
  position_x: number;
  position_y: number;
  color: string | null;
  icon: string | null;
  properties: Record<string, unknown> | string | null;
}

interface RelationshipData {
  id: string;
  source_entity_id: string;
  target_entity_id: string;
  relationship_type: string;
  label: string | null;
  weight: number;
  confidence: number;
  color: string | null;
}

function entityToNode(entity: EntityData): Node {
  let parsedProps: Record<string, unknown> = {};
  if (entity.properties) {
    if (typeof entity.properties === 'string') {
      try { 
        if (entity.properties !== '[object Object]') {
          parsedProps = JSON.parse(entity.properties); 
        }
      } catch (e) { 
        console.warn('Failed to parse properties for entity', entity.id, entity.properties);
        parsedProps = {}; 
      }
    } else if (typeof entity.properties === 'object') {
      parsedProps = entity.properties as Record<string, unknown>;
    }
  }
  return {
    id: entity.id,
    type: 'entity',
    position: { x: entity.position_x, y: entity.position_y },
    data: {
      label: entity.label,
      value: entity.value,
      entityType: entity.entity_type,
      confidence: entity.confidence,
      source: entity.source,
      color: entity.color,
      icon: entity.icon,
      properties: parsedProps,
    },
  };
}

function relationshipToEdge(rel: RelationshipData, nodes: Node[], layoutMode: LayoutMode = 'smart_force'): Edge {
  const targetNode = nodes.find(n => n.id === rel.target_entity_id);
  const targetType = (targetNode?.data?.entityType as string) || 'custom';
  const targetColor = (targetNode?.data?.color as string) || COLOR_MAP[targetType] || rel.color || '#475569';

  return {
    id: rel.id,
    source: rel.source_entity_id,
    target: rel.target_entity_id,
    type: layoutMode === 'intelligence_concept' ? 'smoothstep' : 'smart',
    animated: rel.confidence < 0.5,
    style: {
      stroke: targetColor,
      strokeWidth: Math.max(1, Math.min(3, rel.weight)),
    },
    markerEnd: {
      type: MarkerType.ArrowClosed,
      width: 14,
      height: 14,
      color: targetColor,
    },
    data: {
      relationshipType: rel.relationship_type,
      weight: rel.weight,
      confidence: rel.confidence,
    },
  };
}

function InvestigationCanvas() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const reactFlowInstance = useReactFlow();
  const { 
    setSelectedNode: setGraphStoreSelectedNode, setSelectedNodes, 
    setHoveredNode, clearHighlights, layoutMode, clusterThreshold, 
    collapsedClusters, hiddenEntityTypes, selectedNodeIds 
  } = useGraphStore();
  const { sidebarOpen, toggleSidebar, rightPanelOpen, toggleRightPanel } = useUIStore();
  const { addLog } = useConsoleStore();

  const [investigation, setInvestigation] = useState<InvestigationData | null>(null);
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [loading, setLoading] = useState(true);

  const nodesRef = useRef<Node[]>([]);
  const edgesRef = useRef<Edge[]>([]);

  useEffect(() => {
    nodesRef.current = nodes;
  }, [nodes]);

  useEffect(() => {
    edgesRef.current = edges;
  }, [edges]);

  const [activeView, setActiveView] = useState<'graph' | 'table' | 'timeline' | 'map' | 'matrix' | 'kanban' | 'dashboard'>('graph');

  // History State for Undo/Redo
  const [past, setPast] = useState<{nodes: Node[], edges: Edge[]}[]>([]);
  const [future, setFuture] = useState<{nodes: Node[], edges: Edge[]}[]>([]);

  const pushHistory = (currentNodes: Node[], currentEdges: Edge[]) => {
    setPast(p => [...p.slice(-50), { nodes: currentNodes, edges: currentEdges }]);
    setFuture([]);
  };

  const handleUndo = useCallback(() => {
    if (past.length === 0) return;
    const previous = past[past.length - 1];
    setFuture(f => [{ nodes, edges }, ...f]);
    setPast(p => p.slice(0, -1));
    setNodes(previous.nodes);
    setEdges(previous.edges);
  }, [past, nodes, edges, setNodes, setEdges]);

  const handleRedo = useCallback(() => {
    if (future.length === 0) return;
    const next = future[0];
    setPast(p => [...p, { nodes, edges }]);
    setFuture(f => f.slice(1));
    setNodes(next.nodes);
    setEdges(next.edges);
  }, [future, nodes, edges, setNodes, setEdges]);
  const [bottomPanelOpen, setBottomPanelOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const reactFlowWrapper = useRef<HTMLDivElement>(null);

  const [showAddEntity, setShowAddEntity] = useState(false);
  const [showFilterPanel, setShowFilterPanel] = useState(false);
  const [showAutoInvestigateModal, setShowAutoInvestigateModal] = useState(false);
  const [newEntityType, setNewEntityType] = useState('domain');
  const [newEntityValue, setNewEntityValue] = useState('');
  const [saving, setSaving] = useState(false);
  const [contextMenu, setContextMenu] = useState<{ x: number; y: number; node: Node } | null>(null);

  const undo = handleUndo;
  const redo = handleRedo;

  const handleNodeContextMenu = useCallback((event: React.MouseEvent, node: Node) => {
    event.preventDefault();
    setContextMenu({ x: event.clientX, y: event.clientY, node });
  }, []);

  const handleDeleteNode = async (nodeId: string) => {
    try {
      await apiClient.delete(`/entities/${nodeId}`);
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
      if (selectedNode?.id === nodeId) setSelectedNode(null);
    } catch (err) {
      console.error('Failed to delete node:', err);
    }
  };

  useOnSelectionChange({
    onChange: ({ nodes }) => {
      setSelectedNodes(nodes.map(n => n.id));
    },
  });

  // Effect to handle Entity Visibility toggles
  useEffect(() => {
    setNodes((nds) => nds.map((n) => {
      if (n.type === 'entity' && n.data?.entityType) {
        return { ...n, hidden: hiddenEntityTypes.has(n.data.entityType as string) };
      }
      return n;
    }));
  }, [hiddenEntityTypes, setNodes]);

  const handleCenterNode = (node: Node) => {
    reactFlowInstance.setCenter(node.position.x + 80, node.position.y + 40, { zoom: 1.2, duration: 400 });
  };

  const handleRunTransformFromContext = async (transformId: string) => {
    if (!contextMenu || !id) return;
    const targetNodeId = contextMenu.node.id;
    const targetVal = (contextMenu.node.data?.value as string) || (contextMenu.node.data?.label as string) || 'Target';
    const queueId = `${transformId}-${Date.now()}`;
    const tStart = performance.now();

    useConsoleStore.getState().addQueueItem({
      id: queueId,
      transformId,
      targetValue: targetVal,
      status: 'running',
    });
    addLog('INFO', `Executing ${transformId} on ${targetVal}...`);

    try {
      const { data } = await apiClient.post('/transforms/execute', {
        investigation_id: id,
        transform_id: transformId,
        input_entity_id: targetNodeId,
      });
      const dur = (performance.now() - tStart) / 1000;
      useConsoleStore.getState().updateQueueItem(queueId, {
        status: 'completed',
        durationSeconds: dur,
        entitiesCreated: data.entities_created || 0,
        relationshipsCreated: data.relationships_created || 0,
      });
      addLog('SUCCESS', `${transformId} completed: +${data.entities_created || 0} entities, +${data.relationships_created || 0} relationships`);
      loadInvestigation(id, false, false, targetNodeId);
    } catch (err: any) {
      const dur = (performance.now() - tStart) / 1000;
      useConsoleStore.getState().updateQueueItem(queueId, {
        status: 'failed',
        durationSeconds: dur,
      });
      addLog('ERROR', `Failed to execute ${transformId}: ${err?.response?.data?.message || err?.message || 'Error'}`);
      console.error('Failed to execute transform from context menu:', err);
    }
  };

  const [autoInvestigating, setAutoInvestigating] = useState(false);

  const startAutoInvestigation = async (depth: number = 10, maxEntities: number = 500, allowedTransforms: string[] | null = null) => {
    if (!id) return;
    setAutoInvestigating(true);
    try {
      await apiClient.post(`/investigations/${id}/auto-investigate`, {
        root_entity_id: selectedNode?.id || null,
        max_depth: depth,
        max_entities: maxEntities,
        allowed_transforms: allowedTransforms,
      });
    } catch (err) {
      console.error('Failed to launch auto investigation:', err);
      setAutoInvestigating(false);
    }
  };

  const stopAutoInvestigation = async () => {
    if (!id) return;
    try {
      await apiClient.post(`/investigations/${id}/auto-investigate/stop`);
      setAutoInvestigating(false);
      addLog('WARNING', 'Auto-investigation stopped by user.');
    } catch (err) {
      console.error('Failed to stop auto investigation:', err);
      addLog('ERROR', 'Failed to stop auto investigation.');
    }
  };

  useEffect(() => {
    if (!id) return;
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host;
    const ws = new WebSocket(`${protocol}//${host}/ws/investigation/${id}`);
    try {
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Log WebSocket events to Console
          if (data.type === 'auto_investigation_started') {
            setAutoInvestigating(true);
            addLog('INFO', `Investigation sweep started (Max Depth: ${data.max_depth}, Max Entities: ${data.max_entities})`);
          } else if (data.type === 'transform_executing') {
            const queueId = `${data.transform_id}-${data.entity_id || Date.now()}`;
            useConsoleStore.getState().addQueueItem({
              id: queueId,
              transformId: data.transform_id,
              targetValue: data.entity_value || 'Target',
              status: 'running',
            });
            addLog('INFO', `Executing transform: ${data.transform_id} on ${data.entity_value || 'target'}...`);
          } else if (data.type === 'graph_updated') {
            addLog('SUCCESS', `Graph updated: +${data.entities_created} new entities discovered`);
            // Live simultaneous rendering: fetch new nodes and attach them in real-time
            loadInvestigation(id, false, false, data.entity_id);
          } else if (data.type === 'auto_investigation_completed') {
            setAutoInvestigating(false);
            addLog('SUCCESS', `Investigation sweep completed at depth ${data.final_depth}`);
            loadInvestigation(id, false, false);
          } else {
            addLog('INFO', `Received WS event: ${data.type}`);
          }
        } catch (e) {
          console.error('WebSocket parse error:', e);
        }
      };
    } catch (e) {
      console.error('WebSocket connection error:', e);
    }
    return () => ws?.close();
  }, [id]);

  // Live polling interval while auto-investigation is active so new discoveries render instantly
  useEffect(() => {
    if (!autoInvestigating || !id) return;
    const interval = setInterval(() => {
      loadInvestigation(id);
    }, 1200);
    return () => clearInterval(interval);
  }, [autoInvestigating, id]);

  useEffect(() => {
    if (id) {
      useConsoleStore.getState().clearAll();
      loadInvestigation(id, true);
    }
  }, [id]);

  useEffect(() => {
    if (nodes.length > 0 && edges.length > 0) {
      applyAutoLayout();
    }
  }, [layoutMode, clusterThreshold, collapsedClusters]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        undo();
      }
      if ((e.ctrlKey || e.metaKey) && (e.key === 'y' || (e.key === 'z' && e.shiftKey))) {
        e.preventDefault();
        redo();
      }
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        savePositions();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [nodes]);

  const loadInvestigation = async (investigationId: string, showSpinner = false, isInitial = false, targetNodeId?: string) => {
    try {
      if (showSpinner) setLoading(true);
      const [invRes, entRes, relRes] = await Promise.all([
        apiClient.get<InvestigationData>(`/investigations/${investigationId}`),
        apiClient.get<PaginatedResponse<EntityData>>(`/entities?investigation_id=${investigationId}&page_size=5000`),
        apiClient.get<PaginatedResponse<RelationshipData>>(`/relationships?investigation_id=${investigationId}&page_size=5000`),
      ]);

      setInvestigation(invRes.data);
      
      const rawNodes = entRes.data.items.map(entityToNode);
      const rawEdges = relRes.data.items.map((rel: any) => relationshipToEdge(rel, rawNodes, layoutMode));
      
      const currentNodes = nodesRef.current;
      const isFirstLoad = isInitial || currentNodes.length === 0;

      if (isFirstLoad) {
        // If all nodes have default (0, 0) coordinates, compute initial layout
        const allAtZero = rawNodes.every(n => n.position.x === 0 && n.position.y === 0);
        if (allAtZero && rawNodes.length > 0) {
          const worker = new LayoutWorker();
          worker.postMessage({
            nodes: rawNodes,
            edges: rawEdges,
            layoutMode,
            clusterThreshold,
            collapsedClusters: Array.from(collapsedClusters),
            rootEntityId: invRes.data.root_entity_id || (rawNodes.length > 0 ? rawNodes[0].id : undefined),
          });
          
          worker.onmessage = (e) => {
            const { hiddenEntityTypes } = useGraphStore.getState();
            const layoutNodes = e.data.nodes.map((n: Node) => {
              if (n.type === 'entity' && n.data?.entityType) {
                 return { ...n, hidden: hiddenEntityTypes.has(n.data.entityType as string) };
              }
              return n;
            });
            pushHistory(currentNodes, edgesRef.current);
            setNodes(layoutNodes);
            setEdges(e.data.edges || rawEdges);
            worker.terminate();
            addLog('SUCCESS', `Investigation loaded successfully (${layoutNodes.length} nodes)`);

            // Auto-save initial layout positions to server
            const positions = layoutNodes.map((n: Node) => ({
              id: n.id,
              position_x: n.position.x,
              position_y: n.position.y,
            }));
            apiClient.put('/entities/positions/bulk', { positions }).catch(console.error);
          };
          return;
        }
      }

      // INCREMENTAL UPDATE OR PARTIAL LOAD
      const currentNodesMap = new Map<string, Node>();
      currentNodes.forEach((n) => currentNodesMap.set(n.id, n));

      const mergedNodes: Node[] = [];
      const newRawNodes: Node[] = [];

      rawNodes.forEach((serverNode) => {
        const existingNode = currentNodesMap.get(serverNode.id);
        if (existingNode) {
          // STRICTLY PRESERVE THE USER'S DISPLACED POSITION
          mergedNodes.push({
            ...serverNode,
            position: { ...existingNode.position },
            data: { ...serverNode.data },
          });
        } else if (isFirstLoad && (serverNode.position.x !== 0 || serverNode.position.y !== 0)) {
          // Keep saved DB position on first load
          currentNodesMap.set(serverNode.id, serverNode);
          mergedNodes.push(serverNode);
        } else {
          // Node is completely new OR lacks a saved DB position (is exactly 0,0)
          newRawNodes.push(serverNode);
        }
      });

      // Group newly discovered nodes by their specific parent node
      const parentToChildren = new Map<string, Node[]>();
      const fallbackParent = (targetNodeId && currentNodesMap.get(targetNodeId)) 
        ? currentNodesMap.get(targetNodeId) 
        : (selectedNode?.id && currentNodesMap.get(selectedNode.id))
          ? currentNodesMap.get(selectedNode.id)
          : null;

      newRawNodes.forEach((newNode) => {
        // Find connecting edge in rawEdges
        const connectedEdges = rawEdges.filter(
          (e) => e.source === newNode.id || e.target === newNode.id
        );

        let parentId: string | undefined;
        if (connectedEdges.length > 0) {
          const edge = connectedEdges[0];
          parentId = edge.source === newNode.id ? edge.target : edge.source;
        } else if (fallbackParent) {
          parentId = fallbackParent.id;
        }

        const effectiveParentId = parentId || (currentNodes.length > 0 ? currentNodes[0].id : undefined);

        if (effectiveParentId) {
          if (!parentToChildren.has(effectiveParentId)) {
            parentToChildren.set(effectiveParentId, []);
          }
          parentToChildren.get(effectiveParentId)!.push(newNode);
        } else {
          newNode.position = {
            x: Math.round((mergedNodes.length % 5) * 220 - 440),
            y: Math.round(Math.floor(mergedNodes.length / 5) * 160 + 200),
          };
          mergedNodes.push(newNode);
        }
      });

      // Distribute children in satellite rings directly around their parent's current displaced position
      parentToChildren.forEach((children, parentId) => {
        const parentNode = currentNodesMap.get(parentId) || mergedNodes.find(n => n.id === parentId);
        if (!parentNode) {
          children.forEach((c, idx) => {
            c.position = { x: (idx % 4) * 300, y: Math.floor(idx / 4) * 150 };
            mergedNodes.push(c);
          });
          return;
        }

        const px = parentNode.position.x;
        const py = parentNode.position.y;
        const total = children.length;

        if (total === 1) {
          children[0].position = { x: px + 350, y: py };
          mergedNodes.push(children[0]);
          return;
        }

        let remaining = total;
        let currentIdx = 0;
        let ringIdx = 0;

        while (remaining > 0) {
          const r = 350 + (ringIdx * 250); // Expanding radius for each ring
          // Calculate max nodes this ring can hold based on 320px minimum arc length per node
          const maxNodesForRing = Math.max(6, Math.floor((2 * Math.PI * r) / 320));
          const nodesInRing = Math.min(remaining, maxNodesForRing);

          for (let i = 0; i < nodesInRing; i++) {
            const angle = (i / nodesInRing) * 2 * Math.PI - Math.PI / 2;
            const child = children[currentIdx];
            child.position = {
              x: Math.round(px + r * Math.cos(angle)),
              y: Math.round(py + r * Math.sin(angle)),
            };
            mergedNodes.push(child);
            currentIdx++;
          }

          remaining -= nodesInRing;
          ringIdx++;
        }
      });

      const { hiddenEntityTypes } = useGraphStore.getState();
      const finalNodes = mergedNodes.map((n) => {
        if (n.type === 'entity' && n.data?.entityType) {
          return { ...n, hidden: hiddenEntityTypes.has(n.data.entityType as string) };
        }
        return n;
      });

      pushHistory(currentNodes, edgesRef.current);
      setNodes(finalNodes);
      setEdges(rawEdges);

      // Smoothly pan camera to target node if new entities were added
      if (newRawNodes.length > 0) {
        if (targetNodeId && currentNodesMap.get(targetNodeId)) {
          const focusNode = currentNodesMap.get(targetNodeId)!;
          reactFlowInstance.setCenter(focusNode.position.x + 80, focusNode.position.y + 40, { zoom: 0.95, duration: 400 });
        } else {
          setTimeout(() => {
            reactFlowInstance.fitView({ padding: 0.25, duration: 500 });
          }, 60);
        }
      }

      // Auto-save positions to backend so server DB is in sync
      if (newRawNodes.length > 0) {
        const positionsToSave = finalNodes.map((n) => ({
          id: n.id,
          position_x: n.position.x,
          position_y: n.position.y,
        }));
        apiClient.put('/entities/positions/bulk', { positions: positionsToSave }).catch(console.error);
      }

      addLog('SUCCESS', `Graph updated (+${newRawNodes.length} new entities)`);
      
    } catch (err) {
      console.error('Failed to load investigation:', err);
      addLog('ERROR', 'Failed to load investigation graph data.');
    } finally {
      if (showSpinner) setLoading(false);
    }
  };

  const onConnect = useCallback(
    async (connection: Connection) => {
      if (!id || !connection.source || !connection.target) return;
      try {
        const { data } = await apiClient.post('/relationships', {
          investigation_id: id,
          source_entity_id: connection.source,
          target_entity_id: connection.target,
          relationship_type: 'related_to',
        });
        pushHistory(nodes, edges);
        setEdges((eds) =>
          addEdge(
            {
              ...connection,
              id: data.id,
              type: 'smart',
              label: 'related to',
              markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: '#475569' },
              style: { stroke: '#475569', strokeWidth: 1.5 },
            },
            eds,
          ),
        );
      } catch (err) {
        console.error('Failed to create relationship:', err);
      }
    },
    [id, setEdges, nodes, edges],
  );

  const onNodeClick = useCallback((_event: React.MouseEvent, node: Node) => {
    setSelectedNode(node);
    
    // Highlight connected edges and nodes on selection
    const connectedEdges = edges.filter(e => e.source === node.id || e.target === node.id);
    const connectedNodeIds = connectedEdges.flatMap(e => [e.source, e.target]);
    
    setGraphStoreSelectedNode(node.id, connectedNodeIds, connectedEdges.map(e => e.id));
    useUIStore.getState().setRightPanelTab('details');
    setContextMenu(null);
  }, [setGraphStoreSelectedNode, edges]);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
    clearHighlights();
    setContextMenu(null);
  }, [clearHighlights]);

  const onNodeMouseEnter = useCallback((_: React.MouseEvent, node: Node) => {
    // Find connected edges and nodes
    const connectedEdges = edges.filter(e => e.source === node.id || e.target === node.id);
    const connectedNodeIds = connectedEdges.flatMap(e => [e.source, e.target]);
    setHoveredNode(node.id, connectedNodeIds, connectedEdges.map(e => e.id));
  }, [edges, setHoveredNode]);

  const onNodeMouseLeave = useCallback(() => {
    setHoveredNode(null);
  }, [setHoveredNode]);

  const parseTargetInput = (val: string, type: string) => {
    let raw = val.trim();
    let label = raw;
    let cleanVal = raw;

    // 1. Check for markdown link: [Label](https://...)
    const mdMatch = raw.match(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/);
    if (mdMatch) {
      label = mdMatch[1].trim() || mdMatch[2].trim();
      cleanVal = mdMatch[2].trim();
    }

    // 2. Normalize based on target type
    if (type === 'domain' || type === 'subdomain' || type === 'ip_address') {
      cleanVal = cleanVal.replace(/^https?:\/\//i, '').split('/')[0].split('?')[0].split('#')[0].trim().toLowerCase();
      if (cleanVal.startsWith('www.')) {
        cleanVal = cleanVal.substring(4);
      }
      if (!mdMatch) {
        label = cleanVal;
      }
    } else if (type === 'email') {
      cleanVal = cleanVal.replace(/^mailto:/i, '').trim().toLowerCase();
      if (!mdMatch) label = cleanVal;
    } else if (type === 'website' || type === 'url') {
      if (!cleanVal.startsWith('http://') && !cleanVal.startsWith('https://')) {
        cleanVal = `https://${cleanVal}`;
      }
    }

    return { label, value: cleanVal };
  };

  const addEntity = async (customValue?: string, customType?: string) => {
    const rawVal = customValue || newEntityValue;
    const targetType = customType || newEntityType;
    if (!id || !rawVal.trim()) return;

    const { label, value: val } = parseTargetInput(rawVal, targetType);

    try {
      const position = reactFlowInstance.screenToFlowPosition({
        x: window.innerWidth / 2,
        y: window.innerHeight / 2,
      });

      const { data } = await apiClient.post('/entities', {
        investigation_id: id,
        entity_type: targetType,
        label: label,
        value: val,
        position_x: position.x,
        position_y: position.y,
      });

      const newNode: Node = {
        id: data.id,
        type: 'entity',
        position: { x: position.x, y: position.y },
        data: {
          label: label,
          value: val,
          entityType: targetType,
          confidence: 1.0,
        },
      };

      pushHistory(nodes, edges);
      setNodes((nds) => [...nds, newNode]);
      setSelectedNode(newNode);
      useUIStore.setState({ rightPanelOpen: true, rightPanelTab: 'transforms' });
      setNewEntityValue('');
      setShowAddEntity(false);
    } catch (err) {
      console.error('Failed to add entity:', err);
    }
  };

  const quickAddTarget = (targetName: string) => {
    let raw = targetName.trim();
    let detectedType = 'domain';

    const mdMatch = raw.match(/\[(.*?)\]\((https?:\/\/[^\s)]+)\)/);
    if (mdMatch) {
      raw = mdMatch[2].trim();
    }

    const clean = raw.replace(/^https?:\/\//i, '').split('/')[0].split('?')[0].trim();
    if (/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/.test(clean)) {
      detectedType = 'ip_address';
    } else if (clean.includes('@')) {
      detectedType = 'email';
    } else if (clean.includes('.')) {
      detectedType = clean.split('.').length > 2 ? 'subdomain' : 'domain';
    }
    addEntity(targetName, detectedType);
  };

  const savePositions = async () => {
    if (!id) return;
    setSaving(true);
    try {
      const positions = nodes.map((n) => ({
        id: n.id,
        position_x: n.position.x,
        position_y: n.position.y,
      }));
      await apiClient.put('/entities/positions/bulk', { positions });
    } catch (err) {
      console.error('Failed to save positions:', err);
    } finally {
      setSaving(false);
    }
  };

  const applyAutoLayout = async () => {
    if (!id || nodes.length === 0) return;
    
    // Strip out any virtual cluster nodes from previous galaxy layouts before recalculating
    const entityNodes = nodes.filter(n => n.type !== 'cluster');

    // Instead of calling backend, use our high-performance Web Worker
    const worker = new LayoutWorker();
    worker.postMessage({
      nodes: entityNodes,
      edges: edges,
      layoutMode,
      clusterThreshold,
      collapsedClusters: Array.from(collapsedClusters),
      rootEntityId: investigation?.root_entity_id || (nodes.length > 0 ? nodes[0].id : undefined),
    });
    
    worker.onmessage = (e) => {
      const { type, nodes: newNodes } = e.data;
      if (type === 'layout_complete') {
        const { hiddenEntityTypes } = useGraphStore.getState();
        const layoutNodes = newNodes.map((n: Node) => {
          if (n.type === 'entity' && n.data?.entityType) {
             return { ...n, hidden: hiddenEntityTypes.has(n.data.entityType as string) };
          }
          return n;
        });
        pushHistory(nodes, edges);
        setNodes(layoutNodes);
        
        // Also update edges if the layout mode changed
        setEdges((eds) => eds.map(edge => ({
            ...edge,
            type: layoutMode === 'intelligence_concept' ? 'smoothstep' : 'smart'
        })));

        const animationsEnabled = useGraphStore.getState().animationEnabled ?? true;
        if (animationsEnabled) {
          setTimeout(() => reactFlowInstance.fitView({ padding: 0.2, duration: 800 }), 100);
        } else {
          setTimeout(() => reactFlowInstance.fitView({ padding: 0.2 }), 50);
        }

        // Auto-save the newly laid out positions to the server
        if (id) {
          const positions = layoutNodes.map((n: Node) => ({
            id: n.id,
            position_x: n.position.x,
            position_y: n.position.y,
          }));
          apiClient.put('/entities/positions/bulk', { positions }).catch(console.error);
        }
      }
      worker.terminate();
    };
  };

  const handleCommandPaletteAction = (cmdId: string) => {
    if (cmdId.startsWith('node_')) {
      const nodeId = cmdId.replace('node_', '');
      const node = nodes.find(n => n.id === nodeId);
      if (node) {
        setActiveView('graph');
        setGraphStoreSelectedNode(nodeId);
        reactFlowInstance.setCenter(node.position.x + 80, node.position.y + 40, { zoom: 1.2, duration: 400 });
      }
      setCommandPaletteOpen(false);
      return;
    }

    if (cmdId === 'view_graph') setActiveView('graph');
    else if (cmdId === 'view_table') setActiveView('table');
    else if (cmdId === 'view_timeline') setActiveView('timeline');
    else if (cmdId === 'view_map') setActiveView('map');
    else if (cmdId === 'view_matrix') setActiveView('matrix');
    else if (cmdId === 'view_kanban') setActiveView('kanban');
    else if (cmdId === 'view_dashboard') setActiveView('dashboard');
    else if (cmdId === 'action_add_entity') setShowAddEntity(true);
    else if (cmdId === 'action_auto_layout') applyAutoLayout();
    else if (cmdId === 'action_fit_view') reactFlowInstance.fitView({ padding: 0.2 });
    else if (cmdId === 'action_export_json' && id) window.open(`/api/v1/investigations/${id}/export/json`, '_blank');
    else if (cmdId === 'action_export_csv' && id) window.open(`/api/v1/investigations/${id}/export/csv`, '_blank');
    else if (cmdId === 'action_export_graphml' && id) window.open(`/api/v1/investigations/${id}/export/graphml`, '_blank');
  };

  const handleBulkDelete = () => {
    if (selectedNodeIds.size === 0) return;
    pushHistory(nodes, edges);
    setNodes(nds => nds.filter(n => !selectedNodeIds.has(n.id)));
    setEdges(eds => eds.filter(e => !selectedNodeIds.has(e.source) && !selectedNodeIds.has(e.target)));
    setSelectedNodes([]);
    addLog('INFO', `Deleted ${selectedNodeIds.size} nodes from canvas`);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-xs text-slate-400 font-mono">Loading investigation environment...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen flex flex-col bg-slate-950 overflow-hidden">
      {/* Top Application Header */}
      <AppHeader
        investigationName={investigation?.name || 'Investigation'}
        investigationStatus={investigation?.status || 'ACTIVE'}
        activeView={activeView}
        onViewChange={setActiveView}
        onOpenCommandPalette={() => setCommandPaletteOpen(true)}
        onOpenSearch={() => setCommandPaletteOpen(true)}
        onToggleBottomPanel={() => setBottomPanelOpen(!bottomPanelOpen)}
        bottomPanelOpen={bottomPanelOpen}
      />

      {/* Main Investigation Workspace Area */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Navigation Sidebar Drawer */}
        <LeftNavigationSidebar
          onSelectEntityType={(type) => {
            setNewEntityType(type);
            setShowAddEntity(true);
          }}
          onRunTransform={(tId) => handleRunTransformFromContext(tId)}
          isOpen={sidebarOpen}
          onToggle={toggleSidebar}
        />

        {/* Center View Area (Graph / Table / Timeline / Map / Matrix / Kanban) */}
        <div className="flex-1 flex flex-col relative overflow-hidden">
          {activeView === 'graph' && (
            <div className="flex-1 relative bg-transparent grid-bg" ref={reactFlowWrapper}>
              <ReactFlow
                nodes={nodes}
                edges={edges}
                nodeTypes={nodeTypes}
                edgeTypes={edgeTypes}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodeDragStop={(_e, node, draggedNodes) => {
                  pushHistory(nodes, edges);
                  if (id) {
                    const targets = draggedNodes && draggedNodes.length > 0 ? draggedNodes : [node];
                    const positions = targets.map((n) => ({
                      id: n.id,
                      position_x: n.position.x,
                      position_y: n.position.y,
                    }));
                    apiClient.put('/entities/positions/bulk', { positions }).catch((err) => {
                      console.error('Failed to sync dragged node position:', err);
                    });
                  }
                }}
                onConnect={onConnect}
                onNodeClick={onNodeClick}
                onNodeContextMenu={handleNodeContextMenu}
                onNodeMouseEnter={onNodeMouseEnter}
                onNodeMouseLeave={onNodeMouseLeave}
                onPaneClick={onPaneClick}
                onMoveStart={() => setContextMenu(null)}
                fitView
                snapToGrid
                snapGrid={[16, 16]}
                selectionMode={SelectionMode.Partial}
                selectionOnDrag={true}
                panOnDrag={[1, 2]}
                panOnScroll={true}
                deleteKeyCode={['Backspace', 'Delete']}
                multiSelectionKeyCode="Shift"
                minZoom={0.05}
                maxZoom={4}
                defaultEdgeOptions={{
                  type: 'default',
                  markerEnd: { type: MarkerType.ArrowClosed, width: 14, height: 14, color: '#475569' },
                }}
                proOptions={{ hideAttribution: true }}
              >
                <Background variant={BackgroundVariant.Dots} gap={24} size={1} color="rgba(59, 130, 246, 0.1)" />
                <Controls showInteractive={false} position="bottom-left" style={{ marginBottom: 16, marginLeft: 16 }} />
                <MiniMap
                  nodeStrokeWidth={2}
                  zoomable
                  pannable
                  position="bottom-right"
                  style={{ marginBottom: 16, marginRight: rightPanelOpen ? 336 : 16 }}
                  maskColor="rgba(9, 13, 22, 0.85)"
                />
                
                <GraphToolbar />

                {/* Floating Central Glass Dock */}
                <Panel position="top-center" className="mt-4 pointer-events-none w-full flex justify-center z-50">
                  <div className="pointer-events-auto glass bg-slate-900/60 backdrop-blur-xl border border-slate-700/50 shadow-2xl shadow-blue-900/20 rounded-full px-5 py-2.5 flex items-center gap-3 transition-all duration-300 hover:bg-slate-900/80">
                    <button onClick={handleUndo} disabled={past.length === 0} className={`btn btn-ghost rounded-full p-2 ${past.length === 0 ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-800 hover:text-blue-400'}`} title="Undo (Ctrl+Z)">
                      <Undo2 className="w-4 h-4" />
                    </button>
                    <button onClick={handleRedo} disabled={future.length === 0} className={`btn btn-ghost rounded-full p-2 ${future.length === 0 ? 'opacity-40 cursor-not-allowed' : 'hover:bg-slate-800 hover:text-blue-400'}`} title="Redo (Ctrl+Y)">
                      <Redo2 className="w-4 h-4" />
                    </button>
                    
                    <div className="w-px h-5 bg-slate-700/50 mx-1" />
                    
                    <button onClick={applyAutoLayout} className="btn btn-ghost rounded-full p-2 hover:bg-slate-800 hover:text-emerald-400" title="Auto Layout">
                      <Layout className="w-4 h-4" />
                    </button>
                    <button onClick={() => reactFlowInstance.fitView({ padding: 0.2 })} className="btn btn-ghost rounded-full p-2 hover:bg-slate-800 hover:text-emerald-400" title="Fit View">
                      <Maximize2 className="w-4 h-4" />
                    </button>
                    
                    <div className="w-px h-5 bg-slate-700/50 mx-1" />
                    
                    <button onClick={() => id && window.open(`/api/v1/investigations/${id}/export/json`, '_blank')} className="btn btn-ghost rounded-full p-2 hover:bg-slate-800 hover:text-purple-400" title="Export JSON">
                      <Download className="w-4 h-4" />
                    </button>
                    <button onClick={() => id && window.open(`/api/v1/investigations/${id}/export/markdown`, '_blank')} className="btn btn-ghost rounded-full p-2 hover:bg-slate-800 hover:text-purple-400" title="Export Executive Summary (Markdown)">
                      <FileText className="w-4 h-4" />
                    </button>
                    
                    <div className="w-px h-5 bg-slate-700/50 mx-1" />

                    {autoInvestigating ? (
                      <button
                        onClick={stopAutoInvestigation}
                        className="btn rounded-full px-4 py-1.5 bg-red-600/80 hover:bg-red-500 text-white shadow-[0_0_15px_rgba(220,38,38,0.6)] animate-pulse border border-red-400/50 flex items-center gap-2"
                        title="Stop auto-investigation"
                      >
                        <AlertTriangle className="w-4 h-4" />
                        <span className="text-xs font-semibold tracking-wide">STOPPING...</span>
                      </button>
                    ) : (
                      <button
                        onClick={() => setShowAutoInvestigateModal(true)}
                        className="btn rounded-full px-4 py-1.5 bg-emerald-600/80 hover:bg-emerald-500 text-white shadow-[0_0_15px_rgba(16,185,129,0.3)] border border-emerald-400/50 flex items-center gap-2 transition-all hover:scale-105"
                        title="Run recursive OSINT auto-investigation"
                      >
                        <Sparkles className="w-4 h-4" />
                        <span className="text-xs font-semibold tracking-wide">AUTO-INVESTIGATE</span>
                      </button>
                    )}

                    <div className="w-px h-5 bg-slate-700/50 mx-1" />

                    <button onClick={() => setShowAddEntity(true)} className="btn rounded-full px-4 py-1.5 bg-blue-600/80 hover:bg-blue-500 border border-blue-400/50 text-white shadow-[0_0_10px_rgba(59,130,246,0.3)] flex items-center gap-2 transition-all hover:scale-105">
                      <Plus className="w-4 h-4" />
                      <span className="text-xs font-semibold tracking-wide">ADD ENTITY</span>
                    </button>
                    
                    <button onClick={savePositions} disabled={saving} className="btn rounded-full px-4 py-1.5 bg-slate-700/80 hover:bg-slate-600 border border-slate-500/50 text-white flex items-center gap-2">
                      <Save className={`w-4 h-4 ${saving ? 'animate-spin' : ''}`} />
                      <span className="text-xs font-semibold tracking-wide">{saving ? 'SAVING...' : 'SAVE'}</span>
                    </button>
                    
                    <div className="w-px h-5 bg-slate-700/50 mx-1" />
                    
                    <button onClick={() => setShowFilterPanel(!showFilterPanel)} className={`btn rounded-full p-2 transition-all ${showFilterPanel ? 'bg-indigo-500/80 text-white shadow-[0_0_10px_rgba(99,102,241,0.5)]' : 'btn-ghost hover:bg-slate-800'}`} title="Entity Visibility Filters">
                      <Filter className="w-4 h-4" />
                    </button>
                    <button onClick={toggleRightPanel} className={`btn rounded-full p-2 transition-all ${rightPanelOpen ? 'bg-slate-700 text-white' : 'btn-ghost hover:bg-slate-800'}`}>
                      {rightPanelOpen ? <PanelRightClose className="w-4 h-4" /> : <PanelRightOpen className="w-4 h-4" />}
                    </button>
                  </div>
                </Panel>

                {/* Graph Stats Badge */}
                <Panel position="bottom-center" className="mb-4 pointer-events-none flex justify-center w-full z-50">
                  <div className="glass bg-slate-900/40 backdrop-blur-md border border-slate-700/30 shadow-[0_4px_16px_rgba(0,0,0,0.5)] px-4 py-1.5 text-[11px] font-bold tracking-widest text-slate-400 rounded-full flex items-center gap-6">
                    <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-500 shadow-[0_0_8px_#3b82f6]"></div>{nodes.length} ENTITIES</span>
                    <span className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_#10b981]"></div>{edges.length} RELATIONSHIPS</span>
                  </div>
                </Panel>

                {/* Empty State Hero Prompt */}
                {nodes.length === 0 && (
                  <Panel position="top-center" className="mt-20">
                    <div className="bg-slate-900 border border-slate-800 p-6 text-center max-w-sm rounded shadow-2xl">
                      <div className="w-10 h-10 rounded bg-blue-600/20 border border-blue-500/30 flex items-center justify-center mx-auto mb-3 text-blue-400">
                        <Target className="w-5 h-5" />
                      </div>
                      <h3 className="text-sm font-bold text-white mb-1">Start Your Investigation</h3>
                      <p className="text-xs text-slate-400 mb-4">Add your target entity to begin gathering OSINT intelligence.</p>
                      {investigation?.name && (
                        <button
                          onClick={() => quickAddTarget(investigation.name)}
                          className="btn btn-primary w-full text-xs h-8 mb-2 font-mono truncate"
                          title={investigation.name}
                        >
                          <Plus className="w-3.5 h-3.5" /> Add Target: {parseTargetInput(investigation.name, 'domain').value}
                        </button>
                      )}
                      <button onClick={() => setShowAddEntity(true)} className="btn btn-secondary w-full text-xs h-8">
                        Add Custom Entity
                      </button>
                    </div>
                  </Panel>
                )}
              </ReactFlow>

              {/* Multi-Select Action Bar */}
              {selectedNodeIds.size > 1 && (
                <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-50 animate-slide-up">
                  <div className="glass bg-slate-900/80 shadow-2xl border border-slate-700/50 rounded-full px-4 py-2 flex items-center gap-4 backdrop-blur-xl">
                    <span className="text-xs font-semibold text-slate-200">
                      <span className="text-indigo-400 font-bold">{selectedNodeIds.size}</span> nodes selected
                    </span>
                    <div className="w-px h-4 bg-slate-700" />
                    <button onClick={handleBulkDelete} className="btn btn-ghost text-red-400 hover:text-red-300 hover:bg-red-500/10 text-xs py-1 px-3 rounded-full flex items-center">
                      <Trash2 className="w-3.5 h-3.5 mr-1" /> Delete Selected
                    </button>
                  </div>
                </div>
              )}

              {/* Right-Click Context Menu */}
              {contextMenu && (
                <ContextMenu
                  x={contextMenu.x}
                  y={contextMenu.y}
                  node={contextMenu.node}
                  investigationId={id || ''}
                  onClose={() => setContextMenu(null)}
                  onRunTransform={handleRunTransformFromContext}
                  onDeleteNode={handleDeleteNode}
                  onCenterNode={handleCenterNode}
                />
              )}
            </div>
          )}

          {activeView === 'table' && (
            <TableView nodes={nodes} edges={edges} onSelectNode={setSelectedNode} onDeleteNode={handleDeleteNode} />
          )}

          {activeView === 'timeline' && <TimelineView nodes={nodes} onSelectNode={setSelectedNode} />}

          {activeView === 'map' && <MapView nodes={nodes} onSelectNode={setSelectedNode} />}
          {activeView === 'matrix' && <MatrixView nodes={nodes} edges={edges} />}
          {activeView === 'kanban' && <KanbanView />}
          {activeView === 'dashboard' && <DashboardView nodes={nodes} edges={edges} />}
        </div>

        {/* Right Inspector Panel */}
        {rightPanelOpen && (
          <aside className="w-80 glass bg-slate-900/60 backdrop-blur-xl border-l border-slate-700/50 shadow-[-4px_0_24px_rgba(0,0,0,0.5)] overflow-y-auto shrink-0 z-20 transition-all duration-300">
            <EntityPanel
              selectedNode={selectedNode}
              investigationId={id || ''}
              onTransformExecuted={(targetId) => id && loadInvestigation(id, false, false, targetId || selectedNode?.id)}
            />
          </aside>
        )}
      </div>

      {/* Bottom Console Drawer */}
      <BottomPanel
        isOpen={bottomPanelOpen}
        onClose={() => setBottomPanelOpen(false)}
        selectedEntityRawData={selectedNode?.data}
      />

      {/* Command Palette Modal */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
        onSelectCommand={handleCommandPaletteAction}
        nodes={nodes}
      />

      {/* Add Entity Modal */}
      {showAddEntity && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-sm">
          <div className="bg-slate-900 border border-slate-800 p-5 w-full max-w-md rounded shadow-2xl">
            <h3 className="text-sm font-bold text-white uppercase tracking-wider mb-4 border-b border-slate-800 pb-2">
              Add Target Entity
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Entity Type
                </label>
                <select
                  className="input"
                  value={newEntityType}
                  onChange={(e) => setNewEntityType(e.target.value)}
                >
                  <option value="domain">Domain</option>
                  <option value="subdomain">Subdomain</option>
                  <option value="ip_address">IP Address</option>
                  <option value="email">Email</option>
                  <option value="person">Person</option>
                  <option value="organization">Organization</option>
                  <option value="url">URL</option>
                  <option value="username">Username</option>
                  <option value="cve">CVE Vulnerability</option>
                  <option value="wallet">Crypto Wallet</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                  Target Value / Label
                </label>
                <input
                  type="text"
                  className="input font-mono text-xs"
                  placeholder="e.g., drdhanrajchavan.com, 8.8.8.8, octocat"
                  value={newEntityValue}
                  onChange={(e) => setNewEntityValue(e.target.value)}
                  autoFocus
                  onKeyDown={(e) => e.key === 'Enter' && addEntity()}
                />
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <button onClick={() => setShowAddEntity(false)} className="btn btn-secondary text-xs h-8 px-3">
                  Cancel
                </button>
                <button onClick={() => addEntity()} className="btn btn-primary text-xs h-8 px-3">
                  Add Target to Canvas
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {/* Auto Investigate Modal */}
      <AutoInvestigateModal
        isOpen={showAutoInvestigateModal}
        onClose={() => setShowAutoInvestigateModal(false)}
        onStart={startAutoInvestigation}
      />

    </div>
  );
}

export default function Investigation() {
  return (
    <ReactFlowProvider>
      <InvestigationCanvas />
    </ReactFlowProvider>
  );
}

