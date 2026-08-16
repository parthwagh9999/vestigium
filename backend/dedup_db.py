import asyncio
import sys

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select
from sqlalchemy import func

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.config import get_settings

async def main():
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as session:
        print("Deduplicating Entities...")
        # Find duplicates
        result = await session.execute(
            select(
                Entity.investigation_id, 
                Entity.entity_type, 
                Entity.value, 
                func.count(Entity.id).label('c')
            )
            .group_by(Entity.investigation_id, Entity.entity_type, Entity.value)
            .having(func.count(Entity.id) > 1)
        )
        duplicates = result.all()
        
        for inv_id, ent_type, val, count in duplicates:
            # Get all records for this duplicate
            records = (await session.execute(
                select(Entity)
                .where(Entity.investigation_id == inv_id)
                .where(Entity.entity_type == ent_type)
                .where(Entity.value == val)
                .order_by(Entity.created_at)
            )).scalars().all()
            
            keep = records[0]
            drop = records[1:]
            
            print(f"Keeping {keep.id} for {ent_type} '{val}', deleting {len(drop)}")
            
            # Re-point relationships to 'keep'
            for drop_ent in drop:
                # Source rels
                await session.execute(
                    EntityRelationship.__table__.update()
                    .where(EntityRelationship.source_entity_id == drop_ent.id)
                    .values(source_entity_id=keep.id)
                )
                # Target rels
                await session.execute(
                    EntityRelationship.__table__.update()
                    .where(EntityRelationship.target_entity_id == drop_ent.id)
                    .values(target_entity_id=keep.id)
                )
                await session.delete(drop_ent)
                
        await session.commit()
        
        print("Deduplicating Relationships...")
        result = await session.execute(
            select(
                EntityRelationship.investigation_id,
                EntityRelationship.source_entity_id,
                EntityRelationship.target_entity_id,
                EntityRelationship.relationship_type,
                func.count(EntityRelationship.id)
            )
            .group_by(
                EntityRelationship.investigation_id,
                EntityRelationship.source_entity_id,
                EntityRelationship.target_entity_id,
                EntityRelationship.relationship_type,
            )
            .having(func.count(EntityRelationship.id) > 1)
        )
        
        rel_duplicates = result.all()
        for inv_id, src, tgt, rel_type, count in rel_duplicates:
            records = (await session.execute(
                select(EntityRelationship)
                .where(EntityRelationship.investigation_id == inv_id)
                .where(EntityRelationship.source_entity_id == src)
                .where(EntityRelationship.target_entity_id == tgt)
                .where(EntityRelationship.relationship_type == rel_type)
                .order_by(EntityRelationship.created_at)
            )).scalars().all()
            
            drop = records[1:]
            for r in drop:
                await session.delete(r)
                
        await session.commit()
        print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
