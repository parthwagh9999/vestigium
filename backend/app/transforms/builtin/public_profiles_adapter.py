"""Public Profile Correlator across Reddit, GitLab, HackerNews, and Keybase."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class PublicProfilesTransform(BaseTransform):
    """Public Developer & Community Profile Correlator."""

    id = "builtin.public_profiles"
    name = "Public Profile Correlator"
    description = "Correlate public profiles, bios, karma, and identity proofs across Reddit, GitLab, HackerNews, and Keybase."
    category = "Social / Public Profile"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "Public JSON APIs"
    documentation_url = "https://gitlab.com / https://reddit.com"
    license = "MIT"

    input_entity_types = ["username", "person"]
    output_entity_types = ["social_profile", "wallet", "website"]
    relationships_created = ["has_profile", "associated_with"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    installation_required = False
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 15
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        username = entity.value.strip().lstrip("@")

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_results: dict[str, Any] = {}

        async with httpx.AsyncClient(
            timeout=6.0,
            headers={"User-Agent": "Vestigium-OSINT-Investigator/1.0"},
            follow_redirects=True,
        ) as client:
            # 1. HackerNews API
            try:
                hn_resp = await client.get(f"https://hacker-news.firebaseio.com/v0/user/{username}.json")
                if hn_resp.status_code == 200 and hn_resp.json():
                    hn_data = hn_resp.json()
                    raw_results["hackernews"] = hn_data
                    karma = hn_data.get("karma", 0)
                    hn_url = f"https://news.ycombinator.com/user?id={username}"
                    hn_ent = Entity(
                        entity_type="social_profile",
                        value=hn_url,
                        label=f"HackerNews: {username} (Karma: {karma})",
                        confidence=1.0,
                        source="HackerNews API",
                        properties={"karma": karma, "about": hn_data.get("about", ""), "url": hn_url},
                    )
                    entities.append(hn_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=hn_ent.id,
                            relationship_type="has_profile",
                            confidence=1.0,
                            source="HackerNews API",
                            label="hackernews",
                        )
                    )
            except Exception as e:
                logger.debug("HackerNews probe error: %s", e)

            # 2. GitLab API
            try:
                gl_resp = await client.get(f"https://gitlab.com/api/v4/users?username={username}")
                if gl_resp.status_code == 200 and gl_resp.json():
                    gl_users = gl_resp.json()
                    if len(gl_users) > 0:
                        gl_user = gl_users[0]
                        raw_results["gitlab"] = gl_user
                        gl_url = gl_user.get("web_url", f"https://gitlab.com/{username}")
                        gl_ent = Entity(
                            entity_type="social_profile",
                            value=gl_url,
                            label=f"GitLab: {gl_user.get('name', username)}",
                            confidence=1.0,
                            source="GitLab API",
                            properties={"name": gl_user.get("name"), "url": gl_url, "avatar": gl_user.get("avatar_url")},
                        )
                        entities.append(gl_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=gl_ent.id,
                                relationship_type="has_profile",
                                confidence=1.0,
                                source="GitLab API",
                                label="gitlab",
                            )
                        )
            except Exception as e:
                logger.debug("GitLab probe error: %s", e)

            # 3. Keybase API
            try:
                kb_resp = await client.get(f"https://keybase.io/_/api/1.0/user/lookup.json?usernames={username}")
                if kb_resp.status_code == 200:
                    kb_data = kb_resp.json()
                    them = kb_data.get("them", [])
                    if them and len(them) > 0 and them[0] is not None:
                        user_obj = them[0]
                        raw_results["keybase"] = user_obj
                        kb_url = f"https://keybase.io/{username}"
                        kb_ent = Entity(
                            entity_type="social_profile",
                            value=kb_url,
                            label=f"Keybase Identity: {username}",
                            confidence=1.0,
                            source="Keybase API",
                            properties={"url": kb_url, "keybase_id": user_obj.get("id")},
                        )
                        entities.append(kb_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=kb_ent.id,
                                relationship_type="has_profile",
                                confidence=1.0,
                                source="Keybase API",
                                label="keybase",
                            )
                        )
            except Exception as e:
                logger.debug("Keybase probe error: %s", e)

        return entities, relationships, raw_results
