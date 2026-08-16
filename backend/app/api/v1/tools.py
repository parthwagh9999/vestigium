"""OSINT Tool Registry and Health Management API."""

from __future__ import annotations

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_async_session
from app.models.api_key import APIKeyVault
from app.models.entity import Entity
from app.transforms.registry import transform_registry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["tools"])


@router.get("", response_model=List[Dict[str, Any]])
async def list_tools(session: AsyncSession = Depends(get_async_session)):
    """List all registered OSINT tools with truthful live availability status."""
    # Query active API keys to reflect configured status
    result = await session.execute(select(APIKeyVault.service_name).where(APIKeyVault.is_active == True))  # noqa: E712
    configured_keys = set(result.scalars().all())

    # Refresh availability
    transform_registry.refresh_availability(configured_keys)

    tools = []
    for transform in transform_registry.list_all():
        tools.append({
            "id": transform.id,
            "name": transform.name,
            "description": transform.description,
            "category": transform.category,
            "author": transform.author,
            "version": transform.version,
            "source": transform.source,
            "documentation_url": transform.documentation_url,
            "license": transform.license,
            "input_entity_types": transform.input_entity_types,
            "output_entity_types": transform.output_entity_types,
            "relationships_created": transform.relationships_created,
            "execution_type": transform.execution_type,
            "passive_or_active": transform.passive_or_active,
            "authorization_required": transform.authorization_required,
            "api_key_required": transform.api_key_required or transform.requires_api_key,
            "installation_required": transform.installation_required,
            "availability_status": transform.availability_status,
            "installed_version": transform.installed_version,
            "configuration_status": transform.configuration_status,
            "rate_limit": transform.rate_limit,
            "timeout": transform.timeout,
            "supports_recursive_investigation": transform.supports_recursive_investigation,
            "is_passive": transform.is_passive,
            "requires_api_key": transform.requires_api_key,
            "install_status": transform.install_status,
            "supported_os": transform.supported_os,
            "params": [
                {
                    "name": p.name,
                    "display_name": p.display_name,
                    "param_type": p.param_type,
                    "required": p.required,
                }
                for p in transform.params
            ],
        })
    return tools


@router.get("/stats", response_model=Dict[str, Any])
async def get_tool_stats(session: AsyncSession = Depends(get_async_session)):
    """Retrieve statistical breakdown of the OSINT tool ecosystem."""
    result = await session.execute(select(APIKeyVault.service_name).where(APIKeyVault.is_active == True))  # noqa: E712
    configured_keys = set(result.scalars().all())
    transform_registry.refresh_availability(configured_keys)

    stats = transform_registry.get_stats()
    stats["categories"] = transform_registry.get_categories()
    return stats


@router.get("/categories", response_model=List[str])
async def list_categories():
    """Retrieve list of unique OSINT categories."""
    return transform_registry.get_categories()


@router.post("/{tool_id}/health", response_model=Dict[str, Any])
async def check_tool_health(tool_id: str, session: AsyncSession = Depends(get_async_session)):
    """Perform on-demand health check for a specific tool."""
    transform = transform_registry.get(tool_id)
    if not transform:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found in registry")

    result = await session.execute(select(APIKeyVault.service_name).where(APIKeyVault.is_active == True))  # noqa: E712
    configured_keys = set(result.scalars().all())

    status = transform.check_availability(configured_keys)
    return {
        "tool_id": transform.id,
        "name": transform.name,
        "availability_status": status,
        "configuration_status": transform.configuration_status,
        "install_status": transform.install_status,
        "execution_type": transform.execution_type,
        "passive_or_active": transform.passive_or_active,
    }


@router.post("/{tool_id}/test", response_model=Dict[str, Any])
async def run_tool_test(tool_id: str, session: AsyncSession = Depends(get_async_session)):
    """Run a safe, sandboxed test execution of a transform with standard test input."""
    transform = transform_registry.get(tool_id)
    if not transform:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_id}' not found in registry")

    # Sample input based on first compatible entity type
    input_type = transform.input_entity_types[0] if transform.input_entity_types and transform.input_entity_types[0] != "*" else "domain"

    SAMPLE_INPUTS = {
        "domain": "google.com",
        "subdomain": "mail.google.com",
        "website": "https://google.com",
        "url": "https://google.com",
        "ip_address": "8.8.8.8",
        "ipv6_address": "2001:4860:4860::8888",
        "asn": "AS15169",
        "email": "test@example.com",
        "username": "octocat",
        "person": "Linus Torvalds",
        "cve": "CVE-2021-44228",
        "hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "country": "Switzerland",
        "city": "Geneva",
    }

    test_value = SAMPLE_INPUTS.get(input_type, "example.com")
    dummy_entity = Entity(
        id="test-entity-sandbox-01",
        investigation_id="test-investigation-sandbox",
        entity_type=input_type,
        value=test_value,
        label=test_value,
    )

    try:
        entities, relationships, raw_data = await transform.execute(dummy_entity, {})
        return {
            "status": "SUCCESS",
            "tool_id": transform.id,
            "test_input": {"type": input_type, "value": test_value},
            "entities_created": len(entities),
            "relationships_created": len(relationships),
            "sample_entities": [{"type": e.entity_type, "value": e.value, "label": e.label} for e in entities[:5]],
            "raw_output_summary": raw_data,
        }
    except Exception as e:
        logger.error("Test execution failed for %s: %s", tool_id, e)
        return {
            "status": "ERROR",
            "tool_id": transform.id,
            "test_input": {"type": input_type, "value": test_value},
            "error": str(e),
        }
