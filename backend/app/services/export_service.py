"""Service for generating comprehensive OSINT investigation reports."""

from __future__ import annotations

import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.investigation import Investigation
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

async def generate_markdown_report(db: AsyncSession, investigation_id: str) -> str:
    """Generate a comprehensive Markdown OSINT report for an investigation."""
    
    # 1. Fetch Investigation
    stmt_inv = select(Investigation).where(Investigation.id == investigation_id)
    result_inv = await db.execute(stmt_inv)
    investigation = result_inv.scalars().first()
    
    if not investigation:
        return f"# Error: Investigation {investigation_id} not found."
        
    # 2. Fetch Entities
    stmt_ent = select(Entity).where(Entity.investigation_id == investigation_id)
    result_ent = await db.execute(stmt_ent)
    entities = result_ent.scalars().all()
    
    # 3. Fetch Relationships
    stmt_rel = select(EntityRelationship).where(EntityRelationship.investigation_id == investigation_id)
    result_rel = await db.execute(stmt_rel)
    relationships = result_rel.scalars().all()
    
    # Organize entities by type
    entities_by_type: dict[str, list[Entity]] = {}
    for entity in entities:
        t = entity.entity_type
        if t not in entities_by_type:
            entities_by_type[t] = []
        entities_by_type[t].append(entity)
        
    # Build Report
    lines = []
    lines.append(f"# VESTIGIUM OSINT Report")
    lines.append(f"**Target/Subject:** {investigation.name}")
    lines.append(f"**Description:** {investigation.description or 'No description provided.'}")
    lines.append(f"**Generated On:** {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append(f"**Status:** {investigation.status}")
    lines.append("---")
    
    # Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append(f"The investigation into **{investigation.name}** yielded **{len(entities)}** unique entities connected by **{len(relationships)}** relationships.")
    
    if entities_by_type:
        lines.append("Key entity breakdown:")
        for t, ents in sorted(entities_by_type.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            lines.append(f"- **{t.upper()}**: {len(ents)} discovered")
    lines.append("---")
    
    # Entity Inventory
    lines.append("## 2. Entity Inventory")
    for t, ents in sorted(entities_by_type.items()):
        lines.append(f"### {t.replace('_', ' ').title()}s ({len(ents)})")
        for ent in sorted(ents, key=lambda x: x.value):
            conf_str = f"{int(ent.confidence * 100)}%"
            lines.append(f"- **{ent.value}** (Confidence: {conf_str})")
        lines.append("")
    lines.append("---")
    
    # Relationship Analysis
    lines.append("## 3. Relationship Analysis")
    if not relationships:
        lines.append("No relationships discovered.")
    else:
        # Create a lookup for entity labels
        entity_lookup = {e.id: e.value for e in entities}
        
        for rel in relationships[:100]: # Limit to 100 to avoid massive markdown
            source_val = entity_lookup.get(rel.source_entity_id, "Unknown")
            target_val = entity_lookup.get(rel.target_entity_id, "Unknown")
            lines.append(f"- `{source_val}` **--[{rel.relationship_type.upper()}]-->** `{target_val}`")
            
        if len(relationships) > 100:
            lines.append(f"\n*(Truncated {len(relationships) - 100} additional relationships)*")
            
    lines.append("---")
    
    # Sources / Tools
    lines.append("## 4. Methodology & Sources")
    lines.append("Intelligence was gathered using authorized passive reconnaissance and open-source intelligence tools.")
    lines.append("All entities were deduplicated and normalized through the Vestigium Entity Resolver pipeline.")
    
    return "\n".join(lines)
