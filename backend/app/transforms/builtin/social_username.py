"""Social media username search transform across major web platforms."""
from __future__ import annotations
import asyncio
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

PLATFORMS = [
    {"name": "GitHub", "url_template": "https://github.com/{}", "type": "github_user", "color": "#181717"},
    {"name": "Twitter / X", "url_template": "https://x.com/{}", "type": "twitter_profile", "color": "#1DA1F2"},
    {"name": "Reddit", "url_template": "https://www.reddit.com/user/{}/", "type": "reddit_profile", "color": "#FF4500"},
    {"name": "Medium", "url_template": "https://medium.com/@{}", "type": "social_profile", "color": "#000000"},
    {"name": "Dev.to", "url_template": "https://dev.to/{}", "type": "social_profile", "color": "#0A0A0A"},
    {"name": "Keybase", "url_template": "https://keybase.io/{}", "type": "social_profile", "color": "#33A0FF"},
    {"name": "Telegram", "url_template": "https://t.me/{}", "type": "telegram_profile", "color": "#26A5E4"},
    {"name": "GitLab", "url_template": "https://gitlab.com/{}", "type": "gitlab_user", "color": "#FC6D26"},
    {"name": "DockerHub", "url_template": "https://hub.docker.com/u/{}", "type": "social_profile", "color": "#2496ED"},
    {"name": "PyPI", "url_template": "https://pypi.org/user/{}/", "type": "social_profile", "color": "#3775A9"},
    {"name": "npm", "url_template": "https://www.npmjs.com/~{}", "type": "social_profile", "color": "#CB3837"},
]

class UsernameSocialTransform(BaseTransform):
    """Transform to probe presence of a username across multiple social platforms."""
    id = "builtin.username_social_search"
    name = "Social Media Account Enumeration"
    description = "Searches for active social media accounts matching a username across 10+ platforms"
    category = "Social Intelligence"
    
    input_entity_types = ["username", "person"]
    output_entity_types = ["social_profile", "github_user", "twitter_profile", "reddit_profile", "telegram_profile", "gitlab_user", "url"]
    
    is_passive = True
    requires_api_key = False

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        username = entity.value.replace("@", "").strip()
        entities = []
        relationships = []

        async def check_platform(platform: dict[str, str], client: httpx.AsyncClient) -> None:
            profile_url = platform["url_template"].format(username)
            try:
                resp = await client.get(
                    profile_url,
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                    follow_redirects=True,
                )
                if resp.status_code == 200 and "404" not in resp.text.lower() and "page not found" not in resp.text.lower():
                    e = Entity(
                        entity_type=platform["type"],
                        value=f"{platform['name']}: {username}",
                        label=f"{platform['name']} (@{username})",
                        confidence=1.0,
                        source=f"Social Check: {platform['name']}"
                    )
                    entities.append(e)
                    relationships.append(EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=e.id,
                        relationship_type="has_account",
                        confidence=1.0,
                        source=f"Social Check: {platform['name']}"
                    ))
            except Exception:
                pass

        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        async with httpx.AsyncClient(timeout=6.0, limits=limits) as client:
            tasks = [check_platform(p, client) for p in PLATFORMS]
            await asyncio.gather(*tasks, return_exceptions=True)

        return entities, relationships, {"checked_username": username, "found_count": len(entities)}
