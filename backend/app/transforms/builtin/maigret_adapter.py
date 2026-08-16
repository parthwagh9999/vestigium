"""Maigret transform adapter for multi-platform username intelligence."""

from __future__ import annotations

import asyncio
import logging
import shutil
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)

# Core OSINT username endpoints with accurate existence validation
USERNAME_SITES = [
    {"name": "GitHub", "url": "https://github.com/{}", "check_status": 200, "category": "Code / Developer"},
    {"name": "GitLab", "url": "https://gitlab.com/{}", "check_status": 200, "category": "Code / Developer"},
    {"name": "Reddit", "url": "https://www.reddit.com/user/{}", "check_status": 200, "category": "Social Media"},
    {"name": "HackerNews", "url": "https://news.ycombinator.com/user?id={}", "check_status": 200, "category": "Tech Community"},
    {"name": "Medium", "url": "https://medium.com/@{}", "check_status": 200, "category": "Blogging"},
    {"name": "DockerHub", "url": "https://hub.docker.com/v2/users/{}/", "check_status": 200, "category": "Container / Tech"},
    {"name": "Dev.to", "url": "https://dev.to/{}", "check_status": 200, "category": "Developer"},
    {"name": "Keybase", "url": "https://keybase.io/{}", "check_status": 200, "category": "Identity / Crypto"},
    {"name": "ProductHunt", "url": "https://www.producthunt.com/@{}", "check_status": 200, "category": "Tech / Startup"},
    {"name": "Pinterest", "url": "https://www.pinterest.com/{}/", "check_status": 200, "category": "Social Media"},
    {"name": "Vimeo", "url": "https://vimeo.com/{}", "check_status": 200, "category": "Video"},
    {"name": "SoundCloud", "url": "https://soundcloud.com/{}", "check_status": 200, "category": "Audio"},
]


class MaigretTransform(BaseTransform):
    """Maigret Multi-Platform Username Reconnaissance."""

    id = "builtin.maigret"
    name = "Maigret Username Profiler"
    description = "Search username presence across 50+ developer, social, and professional platforms with profile validation."
    category = "Username Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "Maigret / Vestigium Engine"
    documentation_url = "https://github.com/soxoj/maigret"
    license = "MIT"

    input_entity_types = ["username", "person"]
    output_entity_types = ["social_profile", "url", "website"]
    relationships_created = ["has_profile", "owns_account"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    installation_required = False  # Built-in async site prober fallback
    supported_os = ["linux", "windows", "macos"]

    availability_status = "AVAILABLE"
    configuration_status = "CONFIGURED"
    timeout = 25
    supports_recursive_investigation = True

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any],
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        username = entity.value.strip().lstrip("@")

        found_profiles: list[dict[str, str]] = []

        # 1. Try maigret CLI if installed
        bin_path = shutil.which("maigret")
        if bin_path:
            try:
                proc = await asyncio.create_subprocess_exec(
                    bin_path,
                    username,
                    "--timeout", "5",
                    "--json", "-",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
                if stdout:
                    import json
                    data = json.loads(stdout.decode("utf-8", errors="ignore"))
                    for site, site_res in data.get("sites", {}).items():
                        if site_res.get("status") == "FOUND":
                            found_profiles.append({
                                "platform": site,
                                "url": site_res.get("url_user", ""),
                                "category": "Social",
                            })
            except Exception as e:
                logger.debug("Maigret CLI error: %s, using async probe fallback", e)

        # 2. Async concurrent site prober fallback
        if not found_profiles:
            async with httpx.AsyncClient(
                timeout=5.0,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Vestigium-Intel/1.0"},
                follow_redirects=True,
            ) as client:
                tasks = []
                for site in USERNAME_SITES:
                    url = site["url"].format(username)
                    tasks.append(self._check_site(client, site["name"], url, site["category"]))

                results = await asyncio.gather(*tasks, return_exceptions=True)
                for res in results:
                    if isinstance(res, dict) and res.get("found"):
                        found_profiles.append(res)

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []

        for profile in found_profiles:
            profile_url = profile["url"]
            platform = profile["platform"]
            prof_ent = Entity(
                entity_type="social_profile",
                value=profile_url,
                label=f"{platform}: @{username}",
                confidence=0.95,
                source="Maigret",
                properties={
                    "platform": platform,
                    "username": username,
                    "url": profile_url,
                    "category": profile.get("category", "Social"),
                },
            )
            entities.append(prof_ent)

            relationships.append(
                EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=prof_ent.id,
                    relationship_type="has_profile",
                    confidence=0.95,
                    source="Maigret",
                    label=platform.lower(),
                )
            )

        return entities, relationships, {
            "username": username,
            "found_count": len(found_profiles),
            "profiles": found_profiles,
        }

    async def _check_site(self, client: httpx.AsyncClient, name: str, url: str, category: str) -> dict[str, Any]:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                # Basic false-positive filtering
                if "Not Found" not in resp.text and "doesn't exist" not in resp.text:
                    return {"platform": name, "url": url, "category": category, "found": True}
        except Exception:
            pass
        return {"platform": name, "url": url, "found": False}
