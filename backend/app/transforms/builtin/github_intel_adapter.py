"""GitHub Intelligence transform adapter for users, orgs, and repositories."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class GitHubIntelTransform(BaseTransform):
    """GitHub User, Organization, and Repository Intelligence."""

    id = "builtin.github_intel"
    name = "GitHub Developer & Repo Intelligence"
    description = "Discover GitHub public repositories, organization members, primary languages, bio, and associated contact info."
    category = "GitHub & Code Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "GitHub REST API"
    documentation_url = "https://docs.github.com/en/rest"
    license = "MIT"

    input_entity_types = ["username", "organization", "company", "person"]
    output_entity_types = ["repository", "email", "website", "company"]
    relationships_created = ["owns_repository", "has_email", "has_website", "works_at"]

    execution_type = "api"
    passive_or_active = "PASSIVE"
    is_passive = True
    authorization_required = False
    api_key_required = False
    api_key_service = "github"
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
        target_name = entity.value.strip().lstrip("@")
        api_key = params.get("api_key")

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "VESTIGIUM-OSINT",
        }
        if api_key:
            headers["Authorization"] = f"token {api_key}"

        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []
        raw_info: dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            # 1. Fetch User/Org Profile
            try:
                user_resp = await client.get(f"https://api.github.com/users/{target_name}")
                if user_resp.status_code == 200:
                    user_data = user_resp.json()
                    raw_info["profile"] = user_data

                    # Blog / Website
                    blog = user_data.get("blog")
                    if blog:
                        if not blog.startswith("http"):
                            blog = f"https://{blog}"
                        web_ent = Entity(
                            entity_type="website",
                            value=blog,
                            label=f"Website: {blog}",
                            confidence=0.95,
                            source="GitHub API",
                            properties={"url": blog, "github_user": target_name},
                        )
                        entities.append(web_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=web_ent.id,
                                relationship_type="has_website",
                                confidence=0.95,
                                source="GitHub API",
                                label="portfolio",
                            )
                        )

                    # Public Email
                    email = user_data.get("email")
                    if email:
                        email_ent = Entity(
                            entity_type="email",
                            value=email,
                            label=email,
                            confidence=1.0,
                            source="GitHub API",
                            properties={"email": email, "github_user": target_name},
                        )
                        entities.append(email_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=email_ent.id,
                                relationship_type="has_email",
                                confidence=1.0,
                                source="GitHub API",
                                label="public_email",
                            )
                        )

                    # Company
                    company = user_data.get("company")
                    if company:
                        company_clean = company.strip().lstrip("@")
                        comp_ent = Entity(
                            entity_type="organization",
                            value=company_clean,
                            label=f"Org: {company_clean}",
                            confidence=0.9,
                            source="GitHub API",
                            properties={"company_name": company_clean, "github_user": target_name},
                        )
                        entities.append(comp_ent)
                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=comp_ent.id,
                                relationship_type="works_at",
                                confidence=0.9,
                                source="GitHub API",
                                label="organization",
                            )
                        )
            except Exception as e:
                logger.debug("GitHub user fetch error: %s", e)

            # 2. Fetch Repositories
            try:
                repos_resp = await client.get(f"https://api.github.com/users/{target_name}/repos?sort=updated&per_page=10")
                if repos_resp.status_code == 200:
                    repos_data = repos_resp.json()
                    raw_info["repos"] = repos_data
                    for repo in repos_data:
                        repo_name = repo.get("full_name") or repo.get("name")
                        html_url = repo.get("html_url")
                        lang = repo.get("language") or "Code"
                        stars = repo.get("stargazers_count", 0)

                        repo_ent = Entity(
                            entity_type="repository",
                            value=html_url,
                            label=f"{repo_name} [{lang}, ★{stars}]",
                            confidence=1.0,
                            source="GitHub API",
                            properties={
                                "repo_name": repo_name,
                                "url": html_url,
                                "language": lang,
                                "stars": stars,
                                "forks": repo.get("forks_count", 0),
                                "description": repo.get("description", ""),
                            },
                        )
                        entities.append(repo_ent)

                        relationships.append(
                            EntityRelationship(
                                source_entity_id=entity.id,
                                target_entity_id=repo_ent.id,
                                relationship_type="owns_repository",
                                confidence=1.0,
                                source="GitHub API",
                                label="repository",
                            )
                        )
            except Exception as e:
                logger.debug("GitHub repos fetch error: %s", e)

        return entities, relationships, raw_info
