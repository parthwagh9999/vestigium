"""Phase 2-3: Transform testing script.

Tests all registered transforms with valid inputs.
Verifies: entity creation, relationship creation, evidence creation, timeline creation.
"""
import asyncio
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def run_tests():
    from app.config import get_settings
    from app.db.engine import create_engine
    from app.db.session import init_session_factory, get_async_session
    from app.db.base import Base
    from app.transforms.builtin import register_builtin_transforms
    from app.transforms.registry import transform_registry
    from app.transforms.runner import TransformRunner
    from app.repositories.entity import EntityRepository
    from app.models.entity import Entity
    
    settings = get_settings()
    engine = create_engine(settings)
    init_session_factory(engine)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    register_builtin_transforms()
    
    # List all transforms
    all_transforms = transform_registry.list_all()
    print(f"\n{'='*70}")
    print(f"TRANSFORM ENGINE TEST - {len(all_transforms)} transforms registered")
    print(f"{'='*70}\n")
    
    # Test data
    TEST_INVESTIGATION_ID = "7cf83c52-f887-436c-be41-512110df51bb"  # Test Google
    
    results = []
    
    from app.db.session import get_session_factory
    async_session_factory = get_session_factory()
    
    for t in all_transforms:
        print(f"\n--- Testing: {t.name} ({t.id}) ---")
        print(f"  Input types: {t.input_entity_types}")
        print(f"  Output types: {t.output_entity_types}")
        print(f"  Passive: {t.is_passive}")
        print(f"  Requires API key: {t.requires_api_key}")
        
        result = {
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "input_types": t.input_entity_types,
            "output_types": t.output_entity_types,
            "requires_api_key": t.requires_api_key,
            "is_passive": t.is_passive,
        }
        
        # Find a suitable test entity
        async with async_session_factory() as session:
            entity_repo = EntityRepository(session)
            
            test_entity = None
            for input_type in t.input_entity_types:
                if input_type == "*":
                    # Get any entity
                    entities = await entity_repo.get_by_investigation(TEST_INVESTIGATION_ID, limit=1)
                    if entities:
                        test_entity = entities[0]
                        break
                else:
                    entities = await entity_repo.get_by_investigation(
                        TEST_INVESTIGATION_ID, entity_type=input_type, limit=1
                    )
                    if entities:
                        test_entity = entities[0]
                        break
            
            if not test_entity:
                print(f"  STATUS: SKIP (no suitable test entity of type {t.input_entity_types})")
                result["status"] = "SKIP"
                result["reason"] = f"No entity of type {t.input_entity_types} in test investigation"
                results.append(result)
                continue
            
            print(f"  Test entity: {test_entity.value} ({test_entity.entity_type})")
            
            # Execute transform
            try:
                runner = TransformRunner(session)
                run = await runner.execute_transform(
                    investigation_id=TEST_INVESTIGATION_ID,
                    transform_id=t.id,
                    input_entity_id=test_entity.id,
                )
                
                result["status"] = "PASS" if run.status == "completed" else "FAIL"
                result["entities_created"] = run.entities_created
                result["relationships_created"] = run.relationships_created
                result["duration_seconds"] = run.duration_seconds
                result["output_summary"] = run.output_summary
                
                if run.entities_created > 0:
                    result["status"] = "PASS_WITH_DATA"
                elif run.status == "completed":
                    result["status"] = "PASS_NO_NEW_DATA"
                    
                print(f"  STATUS: {result['status']}")
                print(f"  Entities: {run.entities_created}, Relationships: {run.relationships_created}")
                print(f"  Duration: {run.duration_seconds}s")
                
            except Exception as e:
                error_msg = str(e)
                result["status"] = "FAILED"
                result["error"] = error_msg
                
                # Classify error
                if "not installed" in error_msg.lower() or "not found" in error_msg.lower():
                    result["status"] = "NOT_INSTALLED"
                elif "api key" in error_msg.lower():
                    result["status"] = "API_KEY_REQUIRED"
                elif "rate limit" in error_msg.lower() or "429" in error_msg:
                    result["status"] = "RATE_LIMITED"
                elif "timeout" in error_msg.lower():
                    result["status"] = "TIMEOUT"
                    
                print(f"  STATUS: {result['status']}")
                print(f"  Error: {error_msg[:200]}")
        
        results.append(result)
    
    # Check evidence and timeline counts
    async with async_session_factory() as session:
        from sqlalchemy import select, func
        from app.models.evidence import Evidence
        from app.models.timeline import TimelineEvent
        
        ev_count = await session.execute(
            select(func.count()).select_from(Evidence).where(Evidence.investigation_id == TEST_INVESTIGATION_ID)
        )
        tl_count = await session.execute(
            select(func.count()).select_from(TimelineEvent).where(TimelineEvent.investigation_id == TEST_INVESTIGATION_ID)
        )
        evidence_total = ev_count.scalar_one()
        timeline_total = tl_count.scalar_one()
    
    # Summary
    print(f"\n{'='*70}")
    print(f"SUMMARY")
    print(f"{'='*70}")
    
    status_counts = {}
    for r in results:
        s = r["status"]
        status_counts[s] = status_counts.get(s, 0) + 1
    
    for status, count in sorted(status_counts.items()):
        print(f"  {status}: {count}")
    
    print(f"\n  Total transforms: {len(results)}")
    print(f"  Evidence records (Test Google): {evidence_total}")
    print(f"  Timeline events (Test Google): {timeline_total}")
    
    # Write JSON report
    with open("transform_test_report.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Report written to transform_test_report.json")
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run_tests())
