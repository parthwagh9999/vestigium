"""Contradiction Detection Engine.

Analyzes Evidence associated with an Entity to detect conflicting facts.
"""
from __future__ import annotations

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evidence import Evidence
from app.models.entity import Entity

logger = logging.getLogger(__name__)

class ContradictionEngine:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def detect_conflicts(self, entity_id: str) -> list[dict]:
        """
        Analyze evidence for a given entity to identify contradictions.
        Returns a list of conflict dictionaries.
        """
        stmt = select(Evidence).where(Evidence.entity_id == entity_id)
        result = await self.session.execute(stmt)
        evidence_records = result.scalars().all()
        
        if not evidence_records or len(evidence_records) < 2:
            return []
            
        conflicts = []
        
        # Example naive contradiction logic: 
        # For simplicity, if we have two different sources providing evidence of the same type,
        # but with vastly different text or confidence, we might flag it.
        # In a real engine, we'd parse the raw_data JSON to find specific conflicting fields 
        # (e.g., location="Mumbai" vs location="Delhi").
        
        # Here we flag if we have two distinct sources reporting different raw_data for the same entity type.
        seen_sources = {}
        for ev in evidence_records:
            source = ev.source or "unknown"
            if source not in seen_sources:
                seen_sources[source] = ev
            else:
                # Same source, different evidence... usually fine
                pass
                
        # Compare sources against each other
        sources_list = list(seen_sources.items())
        for i in range(len(sources_list)):
            for j in range(i + 1, len(sources_list)):
                src1, ev1 = sources_list[i]
                src2, ev2 = sources_list[j]
                
                # If they are different sources but both have raw_data, 
                # we flag it as a potential conflict if the raw data differs significantly.
                if ev1.raw_data and ev2.raw_data:
                    # simplistic check for demonstration: if lengths differ by > 50% or text is entirely disjoint
                    if ev1.raw_data != ev2.raw_data:
                        conflicts.append({
                            "type": "Data Discrepancy",
                            "severity": "high",
                            "description": f"Conflicting data reported between '{src1}' and '{src2}'.",
                            "evidence_1_id": ev1.id,
                            "evidence_2_id": ev2.id
                        })
                        
        return conflicts
