import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test():
    from app.config import get_settings
    from app.db.engine import create_engine
    from app.db.session import init_session_factory, get_session_factory
    from app.db.base import Base
    from app.transforms.builtin import register_builtin_transforms
    from app.repositories.investigation import InvestigationRepository
    from app.repositories.entity import EntityRepository
    from app.osint.orchestrator import InvestigationOrchestrator

    settings = get_settings()
    engine = create_engine(settings)
    init_session_factory(engine)
    register_builtin_transforms()

    async_session_factory = get_session_factory()
    async with async_session_factory() as session:
        inv_repo = InvestigationRepository(session)
        entity_repo = EntityRepository(session)

        inv = await inv_repo.create(
            name="Orchestrator Verification Test",
            description="Testing Run All Safe OSINT",
            workspace_id="00000000-0000-0000-0000-000000000001",
        )
        
        ent = await entity_repo.create(
            investigation_id=inv.id,
            entity_type="domain",
            value="hassan.ns.cloudflare.com",
            label="hassan.ns.cloudflare.com",
            confidence=1.0,
            source="Test",
        )
        await session.commit()

        print(f"Created test entity: {ent.id} ({ent.value})")

        orchestrator = InvestigationOrchestrator(session, "00000000-0000-0000-0000-000000000001")
        res = await orchestrator.run_all_safe_osint(inv.id, ent.id)
        
        print("\nOrchestrator Result Summary:")
        print("Message:", res.get("message"))
        print(f"Total transforms orchestrated: {len(res.get('results', []))}")
        for r in res.get("results", []):
            print(f" - [{r.get('status').upper()}] {r.get('name', r.get('id'))} (+{r.get('entities_created', 0)} entities, +{r.get('relationships_created', 0)} rels)")

if __name__ == "__main__":
    asyncio.run(test())
