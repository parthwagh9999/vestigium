#!/usr/bin/env python3
"""
Test script for verifying OSINT Transform execution.
Usage: python verify_tool.py <module_name> <class_name> <entity_type> <entity_value>
"""
import sys
import os
import asyncio
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../backend')))

from app.models.entity import Entity

async def main():
    if len(sys.argv) < 5:
        print("Usage: python verify_tool.py <module_name> <class_name> <entity_type> <entity_value>")
        sys.exit(1)

    module_name = sys.argv[1]
    class_name = sys.argv[2]
    entity_type = sys.argv[3]
    entity_value = sys.argv[4]

    try:
        module = __import__(f"app.transforms.builtin.{module_name}", fromlist=[class_name])
        transform_cls = getattr(module, class_name)
    except Exception as e:
        print(f"Failed to import {class_name} from {module_name}: {e}")
        sys.exit(1)

    transform = transform_cls()
    entity = Entity(id="test_entity_1", entity_type=entity_type, value=entity_value)

    print(f"Executing {transform.name} against {entity_value}...")
    try:
        entities, relationships, md = await transform.execute(entity, {})
        print(f"SUCCESS!")
        print(f"  Discovered Entities: {len(entities)}")
        print(f"  Generated Relationships: {len(relationships)}")
        for e in entities:
            print(f"    - [{e.entity_type}] {e.value}")
    except Exception as e:
        print(f"FAILED: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
