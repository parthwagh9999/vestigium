import asyncio
from app.db.engine import create_engine
from app.config import get_settings
from app.db.session import init_session_factory, get_session_factory
from sqlalchemy import select
from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.models.transform import TransformResult, TransformRun

async def fix():
    engine = create_engine(get_settings())
    init_session_factory(engine)
    async_session = get_session_factory()
    
    async with async_session() as session:
        # Fetch all active entities
        ents = (await session.execute(select(Entity).where(Entity.is_deleted == False))).scalars().all()
        rels = (await session.execute(select(EntityRelationship).where(EntityRelationship.is_deleted == False))).scalars().all()
        
        connected_ids = set()
        for r in rels:
            connected_ids.add(r.source_entity_id)
            connected_ids.add(r.target_entity_id)
            
        orphan_ents = [e for e in ents if e.id not in connected_ids]
        print(f"Found {len(orphan_ents)} orphaned entities across database.")
        
        fixed_count = 0
        for o in orphan_ents:
            # Find the transform run that created this entity
            result_item = (await session.execute(
                select(TransformResult).where(TransformResult.entity_id == o.id, TransformResult.result_type == "entity")
            )).scalars().first()
            
            if result_item:
                run = (await session.execute(
                    select(TransformRun).where(TransformRun.id == result_item.transform_run_id)
                )).scalars().first()
                
                if run and run.input_entity_id and run.input_entity_id != o.id:
                    # Determine relationship type
                    rel_type = "discovered"
                    if o.entity_type == "ip_address":
                        rel_type = "resolves_to"
                    elif o.entity_type == "subdomain":
                        rel_type = "has_subdomain"
                    elif o.entity_type == "service":
                        rel_type = "open_port"
                    elif o.entity_type == "domain":
                        rel_type = "associated_domain"
                    elif o.entity_type in ("country", "city"):
                        rel_type = "located_in"
                    elif o.entity_type == "asn":
                        rel_type = "belongs_to_asn"
                        
                    new_rel = EntityRelationship(
                        investigation_id=o.investigation_id,
                        source_entity_id=run.input_entity_id,
                        target_entity_id=o.id,
                        relationship_type=rel_type,
                        label=rel_type.replace("_", " "),
                        confidence=1.0,
                        source=f"Transform: {run.transform_name}",
                    )
                    session.add(new_rel)
                    fixed_count += 1
                    print(f"  Fixed link: {run.input_entity_id} -> {rel_type} -> {o.value} ({o.id})")
                    
        await session.commit()
        print(f"Successfully created {fixed_count} missing relationships.")

if __name__ == "__main__":
    asyncio.run(fix())
