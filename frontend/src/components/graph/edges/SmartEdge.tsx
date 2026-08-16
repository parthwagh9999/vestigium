import React, { memo } from 'react';
import {
  BaseEdge,
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
  useReactFlow,
} from '@xyflow/react';
import { useGraphStore } from '@/stores/graphStore';

function SmartEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  label,
  markerEnd,
  selected,
  source,
  target,
}: EdgeProps) {
  const { getNode } = useReactFlow();
  const { hoveredNodeId, highlightedEdgeIds, selectedNodeId, selectedConnectedEdgeIds } = useGraphStore();
  
  // Inherit color from source node, fallback to style.stroke or gray
  const sourceNode = getNode(source);
  const sourceColor = (sourceNode?.data?.color as string) || (style.stroke as string) || '#475569';
  
  const isConnectedToSelected = selectedNodeId !== null && (source === selectedNodeId || target === selectedNodeId || selectedConnectedEdgeIds.has(id));
  const isHighlighted = highlightedEdgeIds.has(id) || isConnectedToSelected;
  const hasActiveHighlight = hoveredNodeId !== null || selectedNodeId !== null;
  const isFaded = hasActiveHighlight && !isHighlighted;
  const isActive = selected || isHighlighted;
  
  const edgePathParams = {
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  };

  const [edgePath, labelX, labelY] = getBezierPath(edgePathParams);

  return (
    <>
      <BaseEdge
        path={edgePath}
        markerEnd={markerEnd}
        className={isActive ? 'animate-flow-dash' : ''}
        style={{
          ...style,
          stroke: sourceColor,
          strokeWidth: isActive ? 3 : 1.5,
          strokeDasharray: isActive ? '6 6' : 'none',
          opacity: isFaded ? 0.05 : (isActive ? 1 : 0.35),
          transition: 'all 0.3s ease',
          filter: isActive ? `drop-shadow(0 0 6px ${sourceColor})` : 'none',
        }}
        id={id}
      />
      {label && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              pointerEvents: 'all',
              background: 'rgba(15, 23, 42, 0.8)',
              padding: '2px 8px',
              borderRadius: '4px',
              fontSize: '10px',
              color: '#94a3b8',
              border: `1px solid ${sourceColor}40`,
              opacity: isActive ? 1 : isFaded ? 0.05 : 0.35,
              transition: 'opacity 0.3s ease',
              display: isFaded ? 'none' : 'block',
            }}
            className="nodrag nopan"
          >
            {label}
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
}

export default memo(SmartEdge);
