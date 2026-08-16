import asyncio
from app.db.engine import create_engine
from app.config import get_settings
from app.db.session import init_session_factory, get_session_factory
from sqlalchemy import select
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

async def check():
    engine = create_engine(get_settings())
    init_session_factory(engine)
    async_session = get_session_factory()
    inv_id = '7cf83c52-f887-436c-be41-512110df51bb'
    
    async with async_session() as session:
        ents = (await session.execute(select(Entity).where(Entity.investigation_id == inv_id, Entity.is_deleted == False))).scalars().all()
        rels = (await session.execute(select(EntityRelationship).where(EntityRelationship.investigation_id == inv_id, EntityRelationship.is_deleted == False))).scalars().all()
        
        ent_map = {e.id: e for e in ents}
        connected_ids = set()
        for r in rels:
            connected_ids.add(r.source_entity_id)
            connected_ids.add(r.target_entity_id)
            
        print(f"Total active entities: {len(ents)}")
        print(f"Total active relationships: {len(rels)}")
        
        orphan_ents = [e for e in ents if e.id not in connected_ids]
        print(f"Orphan entities count: {len(orphan_ents)}")
        for o in orphan_ents:
            print(f"  - Orphan: id={o.id}, type={o.entity_type}, val={o.value}, source={o.source}")
            
        for r in rels:
            src = ent_map.get(r.source_entity_id)
            tgt = ent_map.get(r.target_entity_id)
            if not src or not tgt:
                print(f"  Broken rel: {r.id}, src_found={src is not None} ({r.source_entity_id}), tgt_found={tgt is not None} ({r.target_entity_id}), type={r.relationship_type}")

        for e in ents:
            if '25' in e.value or '134.102' in e.value:
                src_rels = [r for r in rels if r.source_entity_id == e.id]
                tgt_rels = [r for r in rels if r.target_entity_id == e.id]
                print(f"\nNode: {e.value} ({e.entity_type}, id={e.id}):")
                print(f"  Outgoing rels: {len(src_rels)}")
                for r in src_rels:
                    tgt_name = ent_map[r.target_entity_id].value if r.target_entity_id in ent_map else 'MISSING'
                    print(f"    -> {r.relationship_type} -> {tgt_name}")
                print(f"  Incoming rels: {len(tgt_rels)}")
                for r in tgt_rels:
                    src_name = ent_map[r.source_entity_id].value if r.source_entity_id in ent_map else 'MISSING'
                    print(f"    <- {r.relationship_type} <- {src_name}")

if __name__ == "__main__":
    asyncio.run(check())
