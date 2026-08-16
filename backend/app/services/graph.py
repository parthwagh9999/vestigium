"""Graph analysis service using NetworkX.

Provides graph statistics, pathfinding, centrality analysis,
community detection, and layout computations.
"""

from __future__ import annotations

import logging
import math
from typing import Any

import networkx as nx
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.repositories.entity import EntityRepository
from app.repositories.relationship import RelationshipRepository

logger = logging.getLogger(__name__)


class GraphService:
    """Service for NetworkX-based graph analysis operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.entity_repo = EntityRepository(session)
        self.relationship_repo = RelationshipRepository(session)

    async def build_networkx_graph(self, investigation_id: str) -> nx.DiGraph:
        """Build a NetworkX directed graph from investigation data.

        Args:
            investigation_id: The investigation to build the graph for.

        Returns:
            NetworkX DiGraph populated with entities and relationships.
        """
        entities = await self.entity_repo.get_by_investigation(investigation_id, limit=100000)
        relationships = await self.relationship_repo.get_by_investigation(investigation_id, limit=100000)

        graph = nx.DiGraph()

        for entity in entities:
            graph.add_node(
                entity.id,
                entity_type=entity.entity_type,
                label=entity.label,
                value=entity.value,
                confidence=entity.confidence,
            )

        for rel in relationships:
            graph.add_edge(
                rel.source_entity_id,
                rel.target_entity_id,
                relationship_type=rel.relationship_type,
                weight=rel.weight,
                confidence=rel.confidence,
                label=rel.label or rel.relationship_type,
            )

        return graph

    async def get_statistics(self, investigation_id: str) -> dict[str, Any]:
        """Compute graph statistics for an investigation.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Dictionary of graph statistics.
        """
        graph = await self.build_networkx_graph(investigation_id)

        if graph.number_of_nodes() == 0:
            return {
                "node_count": 0,
                "edge_count": 0,
                "density": 0.0,
                "is_connected": False,
                "connected_components": 0,
                "avg_degree": 0.0,
                "max_degree": 0,
                "isolated_nodes": 0,
            }

        undirected = graph.to_undirected()
        degrees = [d for _, d in graph.degree()]

        stats: dict[str, Any] = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "density": round(nx.density(graph), 4),
            "is_connected": nx.is_weakly_connected(graph),
            "connected_components": nx.number_weakly_connected_components(graph),
            "avg_degree": round(sum(degrees) / len(degrees), 2) if degrees else 0.0,
            "max_degree": max(degrees) if degrees else 0,
            "isolated_nodes": len(list(nx.isolates(graph))),
        }

        if graph.number_of_nodes() < 10000:
            entity_type_dist = await self.entity_repo.get_type_distribution(investigation_id)
            rel_type_dist = await self.relationship_repo.get_type_distribution(investigation_id)
            stats["entity_type_distribution"] = entity_type_dist
            stats["relationship_type_distribution"] = rel_type_dist

        return stats

    async def find_shortest_path(
        self,
        investigation_id: str,
        source_id: str,
        target_id: str,
    ) -> list[str] | None:
        """Find shortest path between two entities.

        Args:
            investigation_id: The investigation ID.
            source_id: Source entity ID.
            target_id: Target entity ID.

        Returns:
            List of entity IDs forming the path, or None if no path exists.
        """
        graph = await self.build_networkx_graph(investigation_id)
        undirected = graph.to_undirected()

        try:
            path = nx.shortest_path(undirected, source_id, target_id)
            return list(path)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return None

    async def get_centrality(self, investigation_id: str) -> dict[str, dict[str, float]]:
        """Compute centrality measures for all entities.

        Args:
            investigation_id: The investigation ID.

        Returns:
            Dictionary with centrality metrics per entity.
        """
        graph = await self.build_networkx_graph(investigation_id)

        if graph.number_of_nodes() == 0:
            return {}

        degree_centrality = nx.degree_centrality(graph)
        betweenness = nx.betweenness_centrality(graph) if graph.number_of_nodes() < 5000 else {}
        pagerank_scores = nx.pagerank(graph) if graph.number_of_nodes() < 10000 else {}

        result: dict[str, dict[str, float]] = {}
        for node_id in graph.nodes():
            result[node_id] = {
                "degree": round(degree_centrality.get(node_id, 0.0), 4),
                "betweenness": round(betweenness.get(node_id, 0.0), 4),
                "pagerank": round(pagerank_scores.get(node_id, 0.0), 6),
            }

        return result

    async def compute_layout(
        self,
        investigation_id: str,
        algorithm: str = "spring",
        **kwargs: Any,
    ) -> dict[str, dict[str, float]]:
        """Compute auto-layout positions for entities.

        Args:
            investigation_id: The investigation ID.
            algorithm: Layout algorithm (spring, circular, shell, kamada_kawai, spectral).
            **kwargs: Additional algorithm parameters.

        Returns:
            Dictionary mapping entity IDs to {x, y} positions.
        """
        graph = await self.build_networkx_graph(investigation_id)

        if graph.number_of_nodes() == 0:
            return {}

        layout_algorithms = {
            "spring": nx.spring_layout,
            "circular": nx.circular_layout,
            "shell": nx.shell_layout,
            "kamada_kawai": nx.kamada_kawai_layout,
            "spectral": nx.spectral_layout,
        }

        layout_fn = layout_algorithms.get(algorithm, nx.spring_layout)

        scale = kwargs.pop("scale", 1000)
        try:
            positions = layout_fn(graph, scale=scale, **kwargs)
        except Exception:
            positions = nx.spring_layout(graph, scale=scale)

        result: dict[str, dict[str, float]] = {}
        for node_id, pos in positions.items():
            x = float(pos[0]) if not math.isnan(pos[0]) else 0.0
            y = float(pos[1]) if not math.isnan(pos[1]) else 0.0
            result[node_id] = {"x": round(x, 2), "y": round(y, 2)}

        return result

    async def find_communities(self, investigation_id: str) -> list[list[str]]:
        """Detect communities/clusters in the investigation graph.

        Args:
            investigation_id: The investigation ID.

        Returns:
            List of communities, each being a list of entity IDs.
        """
        graph = await self.build_networkx_graph(investigation_id)
        undirected = graph.to_undirected()

        if undirected.number_of_nodes() == 0:
            return []

        try:
            communities = nx.community.greedy_modularity_communities(undirected)
            return [list(c) for c in communities]
        except Exception:
            components = list(nx.connected_components(undirected))
            return [list(c) for c in components]
