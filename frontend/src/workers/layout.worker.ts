import * as d3 from 'd3-force';
import * as dagre from '@dagrejs/dagre';

self.onmessage = (event) => {
  const { nodes, edges, layoutMode, clusterThreshold, rootEntityId } = event.data;
  
  if (nodes.length === 0) {
    self.postMessage({ type: 'layout_complete', nodes: [] });
    return;
  }

  // PRE-PROCESS: Scale nodes based on rootEntityId, and reset galaxy-specific properties
  nodes.forEach((n: any) => {
    n.data = n.data || {};
    if (rootEntityId && n.id === rootEntityId) {
        n.data.scale = 3; 
    } else {
        n.data.scale = 1;
    }
    
    // Always reset these before applying a layout, so switching out of galaxy cluster works cleanly
    if (layoutMode !== 'galaxy_cluster') {
        delete n.parentId;
        delete n.hidden;
    }
  });

  let updatedNodes = [...nodes];

  if (layoutMode === 'smart_force') {
    // ---------------------------------------------------------
    // MODE 1: SMART FORCE LAYOUT
    // ---------------------------------------------------------
    const d3Nodes = nodes.map((n: any) => ({ ...n, radius: 120 * (n.data.scale || 1) }));
    const d3Edges = edges.map((e: any) => ({ ...e, source: e.source, target: e.target }));

    const simulation = d3.forceSimulation(d3Nodes)
      .force('link', d3.forceLink(d3Edges).id((d: any) => d.id).distance(150))
      .force('charge', d3.forceManyBody().strength(-600))
      .force('collide', d3.forceCollide().radius((d: any) => d.radius).iterations(4))
      .force('x', d3.forceX(0).strength(0.015))
      .force('y', d3.forceY(0).strength(0.015))
      .stop();

    const iterations = Math.min(300, d3Nodes.length * 2);
    for (let i = 0; i < iterations; ++i) simulation.tick();

    updatedNodes = d3Nodes.map((n: any) => {
      const { index, x, y, vy, vx, fx, fy, radius, ...rest } = n;
      return { ...rest, position: { x, y } };
    });

  } else if (layoutMode === 'circular_layered') {
    // ---------------------------------------------------------
    // MODE 2: CIRCULAR LAYERED (BFS Tree)
    // ---------------------------------------------------------
    // 1. Calculate Indegree
    const inDegree: Record<string, number> = {};
    const outEdges: Record<string, string[]> = {};
    nodes.forEach((n: any) => { inDegree[n.id] = 0; outEdges[n.id] = []; });
    edges.forEach((e: any) => {
      if (inDegree[e.target] !== undefined) inDegree[e.target]++;
      if (outEdges[e.source]) outEdges[e.source].push(e.target);
    });

    // 2. Find Roots (Indegree 0)
    let roots = nodes.filter((n: any) => inDegree[n.id] === 0).map((n: any) => n.id);
    if (roots.length === 0) roots = [nodes[0].id];

    // 3. BFS Depth Assignment
    const depths: Record<string, number> = {};
    let maxDepth = 0;
    const queue = roots.map((id: string) => ({ id, depth: 0 }));
    const visited = new Set<string>();

    while (queue.length > 0) {
      const { id, depth } = queue.shift()!;
      if (!visited.has(id)) {
        visited.add(id);
        depths[id] = depth;
        maxDepth = Math.max(maxDepth, depth);
        (outEdges[id] || []).forEach(child => queue.push({ id: child, depth: depth + 1 }));
      }
    }
    
    // Assign unvisited nodes to maxDepth + 1
    nodes.forEach((n: any) => {
      if (depths[n.id] === undefined) {
        depths[n.id] = maxDepth + 1;
        maxDepth = Math.max(maxDepth, depths[n.id]);
      }
    });

    // 4. Group by depth
    const nodesByDepth: Record<number, any[]> = {};
    for (let i = 0; i <= maxDepth; i++) nodesByDepth[i] = [];
    nodes.forEach((n: any) => nodesByDepth[depths[n.id]].push(n));

    // 5. Assign concentric positions
    updatedNodes = nodes.map((n: any) => {
      const d = depths[n.id];
      const layerNodes = nodesByDepth[d];
      
      if (d === 0 && layerNodes.length === 1) {
        // Root is perfectly centered
        return { ...n, position: { x: 0, y: 0 } };
      }

      // Radius scales with depth and number of nodes to prevent overlap
      // Minimum circumference = layerNodes.length * 200px
      const minRadius = (layerNodes.length * 200) / (2 * Math.PI);
      // Base depth multiplier 300 to prevent overlap with 3x scaled root
      const radius = Math.max(d * 300, minRadius);
      
      const index = layerNodes.findIndex(ln => ln.id === n.id);
      const angle = (index / layerNodes.length) * 2 * Math.PI;
      // Scale radius slightly for nodes that are large
      const scale = n.data.scale || 1;

      return {
        ...n,
        position: {
          x: radius * Math.cos(angle),
          y: radius * Math.sin(angle)
        }
      };
    });
  } else if (layoutMode === 'clustered_circular') {
    // ---------------------------------------------------------
    // MODE 3: CLUSTERED CIRCULAR (Group by Entity Type)
    // ---------------------------------------------------------
    const groups: Record<string, any[]> = {};
    nodes.forEach((n: any) => {
       const t = n.data?.entityType || 'unknown';
       if (!groups[t]) groups[t] = [];
       groups[t].push(n);
    });

    const groupKeys = Object.keys(groups);
    // 2. Assign a macro position to each group (arrange groups in a big circle)
    const macroRadius = Math.max(500, groupKeys.length * 250);
    
    updatedNodes = [];
    groupKeys.forEach((t, i) => {
       const groupNodes = groups[t];
       const macroAngle = (i / groupKeys.length) * 2 * Math.PI;
       const cx = macroRadius * Math.cos(macroAngle);
       const cy = macroRadius * Math.sin(macroAngle);

       // 3. Arrange nodes in this group in a micro circle around (cx, cy)
       // Base micro radius on number of nodes and their scales
       const totalScale = groupNodes.reduce((sum, n) => sum + (n.data.scale || 1), 0);
       const microRadius = Math.max(150, (totalScale * 80) / (2 * Math.PI));
       
       let currentAngle = 0;
       groupNodes.forEach((n) => {
           const scale = n.data.scale || 1;
           const angleShare = scale / totalScale;
           currentAngle += (angleShare * Math.PI); // Add half of share to get to center
           
           updatedNodes.push({
               ...n,
               position: {
                   x: cx + microRadius * Math.cos(currentAngle),
                   y: cy + microRadius * Math.sin(currentAngle)
               }
           });
           
           currentAngle += (angleShare * Math.PI); // Add remaining half
       });
    });
  } else if (layoutMode === 'galaxy_cluster') {
    // ---------------------------------------------------------
    // MODE 4: GALAXY CLUSTER LAYOUT (MACRO & MICRO PHYSICS)
    // ---------------------------------------------------------
    const { collapsedClusters = [] } = event.data;
    const collapsedSet = new Set(collapsedClusters);
    
    const outEdges: Record<string, string[]> = {};
    const inDegree: Record<string, number> = {};
    nodes.forEach((n: any) => { outEdges[n.id] = []; inDegree[n.id] = 0; });
    edges.forEach((e: any) => {
      if (outEdges[e.source]) outEdges[e.source].push(e.target);
      if (inDegree[e.target] !== undefined) inDegree[e.target]++;
    });

    // 1. Identify Clusters
    const clusterParents = nodes.filter((n: any) => outEdges[n.id].length >= clusterThreshold);
    const virtualClusters: any[] = [];
    const clusteredChildren = new Set<string>();
    const childToCluster: Record<string, string> = {};

    clusterParents.forEach((parent: any) => {
      const clusterId = `cluster-${parent.id}`;
      // Filter out children that are ALREADY in another cluster
      const availableChildren = outEdges[parent.id].filter(c => !clusteredChildren.has(c));
      
      // If we no longer have enough children to form a cluster, skip
      if (availableChildren.length < clusterThreshold) return;
      
      const isCollapsed = collapsedSet.has(clusterId);
      
      // Calculate micro-layout (inner solar system) using MULTI-RING distribution
      const rings: string[][] = [];
      let currentRing = 0;
      let nodesInCurrentRing = 0;
      
      availableChildren.forEach(childId => {
        const ringRadius = (currentRing + 1) * 200; // 200px per ring depth
        const maxNodesInRing = Math.max(6, Math.floor((ringRadius * 2 * Math.PI) / 200)); // 200px arc length per node
        
        if (!rings[currentRing]) rings[currentRing] = [];
        rings[currentRing].push(childId);
        nodesInCurrentRing++;
        
        if (nodesInCurrentRing >= maxNodesInRing) {
          currentRing++;
          nodesInCurrentRing = 0;
        }
      });
      
      const maxRadius = Math.max(200, rings.length * 200);
      const width = isCollapsed ? 260 : maxRadius * 2 + 300;
      const height = isCollapsed ? 100 : maxRadius * 2 + 300;

      virtualClusters.push({
        id: clusterId,
        type: 'cluster',
        position: { x: 0, y: 0 },
        data: {
          label: `${parent.data.label} Sub-System`,
          count: availableChildren.length,
          color: parent.data.color,
          isCollapsed,
          width,
          height
        },
        width,
        height,
        radius: isCollapsed ? 140 : maxRadius + 150 // huge collision radius for macro physics
      });

      // Assign children to multi-ring micro-layout
      rings.forEach((ringNodes, ringIndex) => {
        const ringRadius = (ringIndex + 1) * 200;
        ringNodes.forEach((childId: string, idx: number) => {
          clusteredChildren.add(childId);
          childToCluster[childId] = clusterId;
          
          const childNode = nodes.find((n: any) => n.id === childId);
          if (childNode) {
            childNode.parentId = clusterId;
            childNode.hidden = isCollapsed;
            
            if (!isCollapsed) {
              const angle = (idx / ringNodes.length) * 2 * Math.PI;
              childNode.position = {
                x: (width / 2) + ringRadius * Math.cos(angle) - 130,
                y: (height / 2) + ringRadius * Math.sin(angle) - 50
              };
            }
          }
        });
      });
    });

    // 2. Macro-Layout (Inter-Galactic)
    // Only simulate top-level nodes (parents, unclustered, and virtual clusters)
    const topLevelNodes = [
      ...nodes.filter((n: any) => !clusteredChildren.has(n.id)).map((n: any) => ({ ...n, radius: 120 })),
      ...virtualClusters
    ];

    // Build macro edges (ignoring internal cluster edges)
    const macroEdges = edges
      .filter((e: any) => !clusteredChildren.has(e.source) && !clusteredChildren.has(e.target))
      .map((e: any) => ({
        source: e.source,
        target: e.target
      }));

    const simulation = d3.forceSimulation(topLevelNodes)
      .force('link', d3.forceLink(macroEdges).id((d: any) => d.id).distance(400)) // Push clusters further apart
      .force('charge', d3.forceManyBody().strength(-3000)) // Massive repulsion between clusters
      .force('collide', d3.forceCollide().radius((d: any) => d.radius + 50).iterations(8)) // Strict collision
      .force('x', d3.forceX(0).strength(0.01))
      .force('y', d3.forceY(0).strength(0.01))
      .stop();

    const iterations = Math.min(400, topLevelNodes.length * 3);
    for (let i = 0; i < iterations; ++i) simulation.tick();

    // 3. Reassemble Graph
    updatedNodes = [];
    
    // Add clusters
    virtualClusters.forEach(vc => {
      const simNode = topLevelNodes.find(t => t.id === vc.id);
      if (simNode) {
        updatedNodes.push({ ...vc, position: { x: simNode.x, y: simNode.y } });
      }
    });

    // Add normal nodes
    nodes.forEach((n: any) => {
      if (clusteredChildren.has(n.id)) {
        // Child nodes keep their relative positions and parent assignment
        updatedNodes.push(n);
      } else {
        // Top level nodes get simulation positions
        const simNode = topLevelNodes.find(t => t.id === n.id);
        if (simNode) {
          updatedNodes.push({ ...n, position: { x: simNode.x, y: simNode.y } });
        }
      }
    });

  } else if (layoutMode === 'intelligence_concept') {
    // ---------------------------------------------------------
    // MODE 5: INTELLIGENCE CONCEPT MAP (DAGRE HIERARCHY WITH GRID-WRAP)
    // ---------------------------------------------------------
    const g = new dagre.graphlib.Graph();
    g.setGraph({
      rankdir: 'TB',
      nodesep: 200,
      edgesep: 50,
      ranksep: 250,
    });
    g.setDefaultEdgeLabel(() => ({}));

    // Find leaf nodes to grid-wrap
    const inDeg: Record<string, number> = {};
    const outDeg: Record<string, number> = {};
    const parentOf: Record<string, string> = {};
    nodes.forEach((n: any) => { inDeg[n.id] = 0; outDeg[n.id] = 0; });
    edges.forEach((e: any) => {
        inDeg[e.target]++;
        outDeg[e.source]++;
        parentOf[e.target] = e.source; // just grabs the last parent if multiple, but leaf usually has 1
    });

    const leafGroups: Record<string, any[]> = {};
    const isGridWrapped = new Set<string>();

    nodes.forEach((n: any) => {
        // Only wrap true leaves with exactly 1 parent
        if (inDeg[n.id] === 1 && outDeg[n.id] === 0) {
            const pid = parentOf[n.id];
            const type = n.data?.entityType || 'unknown';
            const key = `${pid}-${type}`;
            if (!leafGroups[key]) leafGroups[key] = [];
            leafGroups[key].push(n);
        }
    });

    // Determine which groups actually get wrapped (e.g. > 2 nodes)
    const activeGroups: Record<string, any[]> = {};
    Object.keys(leafGroups).forEach(key => {
        if (leafGroups[key].length > 2) {
            activeGroups[key] = leafGroups[key];
            leafGroups[key].forEach(n => isGridWrapped.add(n.id));
        }
    });

    // Add nodes to dagre
    nodes.forEach((n: any) => {
        if (!isGridWrapped.has(n.id)) {
            const scale = n.data.scale || 1;
            g.setNode(n.id, { width: 260 * scale, height: 80 * scale });
        }
    });

    // Add grid containers to dagre
    Object.keys(activeGroups).forEach(key => {
        const group = activeGroups[key];
        const cols = Math.min(5, group.length); // Max 5 columns wide
        const rows = Math.ceil(group.length / cols);
        g.setNode(`group-${key}`, {
            width: cols * 280, // 260 width + 20 gap
            height: rows * 100 // 80 height + 20 gap
        });
    });

    // Add edges to dagre
    edges.forEach((e: any) => {
        if (isGridWrapped.has(e.target)) {
            // Target is inside a group
            const targetNode = nodes.find((n: any) => n.id === e.target);
            const type = targetNode?.data?.entityType || 'unknown';
            const key = `${e.source}-${type}`;
            // Add edge to the container instead (only once!)
            if (!g.hasEdge(e.source, `group-${key}`)) {
                g.setEdge(e.source, `group-${key}`);
            }
        } else {
            g.setEdge(e.source, e.target);
        }
    });

    // Run dagre layout
    dagre.layout(g);

    updatedNodes = [];
    
    // Apply standard node positions
    nodes.forEach((n: any) => {
        if (!isGridWrapped.has(n.id)) {
            const pos = g.node(n.id);
            if (pos) {
                updatedNodes.push({
                    ...n,
                    position: {
                        x: pos.x - (260 * (n.data.scale || 1)) / 2,
                        y: pos.y - (80 * (n.data.scale || 1)) / 2
                    }
                });
            }
        }
    });

    // Apply grid-wrapped node positions
    Object.keys(activeGroups).forEach(key => {
        const group = activeGroups[key];
        const pos = g.node(`group-${key}`);
        if (pos) {
            const cols = Math.min(5, group.length);
            const startX = pos.x - pos.width / 2;
            const startY = pos.y - pos.height / 2;
            
            group.forEach((n, i) => {
                const col = i % cols;
                const row = Math.floor(i / cols);
                updatedNodes.push({
                    ...n,
                    position: {
                        x: startX + col * 280,
                        y: startY + row * 100
                    }
                });
            });
        }
    });
  }

  self.postMessage({ type: 'layout_complete', nodes: updatedNodes });
};
