import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from app.config import get_settings
from app.db.engine import create_engine
from app.db.session import get_async_session, init_session_factory
from app.models.investigation import Investigation
from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.models.workspace import Workspace
from sqlalchemy import select
import uuid
import json
from datetime import datetime, timezone

async def seed():
    settings = get_settings()
    engine = create_engine(settings)
    init_session_factory(engine)
    session_gen = get_async_session()
    session = await anext(session_gen)
    try:
        workspace_result = await session.execute(select(Workspace).limit(1))
        workspace = workspace_result.scalars().first()
        if not workspace:
            workspace = Workspace(id=str(uuid.uuid4()), name="Test Workspace")
            session.add(workspace)
            await session.commit()
            
        inv_id = str(uuid.uuid4())
        root_id = str(uuid.uuid4())
        
        # 1. Create Investigation
        inv = Investigation(
            id=inv_id,
            workspace_id=workspace.id,
            name="Performance Stress Test 1K",
            status="ACTIVE",
            root_entity_id=root_id
        )
        session.add(inv)
        
        # 2. Create Root Entity
        root = Entity(
            id=root_id,
            investigation_id=inv_id,
            entity_type="domain",
            label="Stress Test Root",
            value="stresstest.internal",
            properties=json.dumps({"label": "Stress Test Root"}),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        session.add(root)
        
        # 3. Create 1000 random children
        print("Creating 1000 entities and relationships...")
        entities = []
        relationships = []
        
        for i in range(1000):
            child_id = str(uuid.uuid4())
            entities.append(
                Entity(
                    id=child_id,
                    investigation_id=inv_id,
                    entity_type="ip_address",
                    label=f"Node {i}",
                    value=f"10.0.{i//256}.{i%256}",
                    properties=json.dumps({"label": f"Node {i}"}),
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            )
            relationships.append(
                EntityRelationship(
                    id=str(uuid.uuid4()),
                    investigation_id=inv_id,
                    source_entity_id=root_id,
                    target_entity_id=child_id,
                    relationship_type="resolves_to"
                )
            )
            
            # Flush every 100 to save RAM
            if i % 100 == 0:
                session.add_all(entities)
                session.add_all(relationships)
                await session.flush()
                entities = []
                relationships = []
        
        if entities:
            session.add_all(entities)
            session.add_all(relationships)
            
        await session.commit()
        print(f"DONE! Seeded investigation {inv_id}")
    finally:
        await session.close()

if __name__ == "__main__":
    asyncio.run(seed())
