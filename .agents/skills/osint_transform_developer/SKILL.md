---
name: OSINT Transform Developer
description: Triggers when the user asks to create, modify, or add an OSINT tool, transform, or adapter.
---

# OSINT Transform Developer Guidelines

You are acting as an OSINT Software Engineer building tools for Nexus Intelligence.

## 1. File Location
All tools are strictly located in `backend/app/transforms/builtin/`. 
Do not create them anywhere else. Register new tools in `backend/app/transforms/builtin/__init__.py`.

## 2. BaseTransform Architecture
Every transform must inherit from `BaseTransform` and implement the `execute` method with this exact signature:

```python
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class MyNewTransform(BaseTransform):
    id = "builtin.my_new_tool"
    name = "My Awesome Tool"
    description = "What it does"
    category = "OSINT"
    
    input_entity_types = ["domain", "ip_address"]
    output_entity_types = ["email", "subdomain"]
    
    is_passive = True # Set to False if it sends traffic to the target
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        
        # 1. Extract value from the input entity
        target = entity.value.strip()
        
        entities = []
        relationships = []
        
        # 2. Perform API calls or lookups here
        # ...
        
        # 3. Create newly discovered entities and link them back
        # IMPORTANT: Relationships must use `source_entity_id` and `target_entity_id`
        e = Entity(entity_type="email", value="test@test.com", label="Email", confidence=1.0, source="MyTool")
        entities.append(e)
        
        rel = EntityRelationship(
            source_entity_id=entity.id,
            target_entity_id=e.id,
            relationship_type="has_email",
            confidence=1.0,
            source="MyTool"
        )
        relationships.append(rel)
        
        # 4. Return strictly typed tuple
        return entities, relationships, {"raw_data": {}}
```

## 3. Strict Rules
- Never use `source_id` or `target_id` inside `EntityRelationship`. It MUST be `source_entity_id` and `target_entity_id`.
- Never return `TransformResponse` or `TransformResultItem`. This was deprecated in Phase 4.
- All network calls must use `httpx.AsyncClient` with a timeout of 10-15 seconds.
- Handle external binary dependencies carefully using graceful degradation (e.g. check if `amass` exists before running it).
