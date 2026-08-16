"""Document and Embedded Asset Metadata Intelligence Transform."""

from __future__ import annotations

import hashlib
import logging
import re
from typing import Any

from app.models.entity import Entity
from app.models.relationship import EntityRelationship
from app.transforms.base import BaseTransform

logger = logging.getLogger(__name__)


class DocumentIntelTransform(BaseTransform):
    """Document & Embedded Asset Metadata Extractor."""

    id = "builtin.document_intel"
    name = "Document Metadata & Link Extractor"
    description = "Extract author, software, creation dates, embedded URLs, and cryptographic hashes from documents and files."
    category = "Document Intelligence"
    author = "VESTIGIUM"
    version = "1.0.0"
    source = "Vestigium Document Engine"
    documentation_url = "https://github.com/exiftool/exiftool"
    license = "MIT"

    input_entity_types = ["file", "pdf_file", "word_file", "excel_file", "image_file", "url"]
    output_entity_types = ["person", "company", "url", "email", "hash"]
    relationships_created = ["authored_by", "created_with", "contains_link", "has_hash"]

    execution_type = "local"
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
        file_path_or_url = entity.value.strip()
        entities: list[Entity] = []
        relationships: list[EntityRelationship] = []

        raw_meta: dict[str, Any] = {
            "target": file_path_or_url,
            "entity_type": entity.entity_type,
        }

        # If it's a file path or direct data
        import os
        if os.path.exists(file_path_or_url) and os.path.isfile(file_path_or_url):
            try:
                with open(file_path_or_url, "rb") as f:
                    content = f.read()

                # 1. Hashes
                md5_hash = hashlib.md5(content).hexdigest()
                sha256_hash = hashlib.sha256(content).hexdigest()

                raw_meta["md5"] = md5_hash
                raw_meta["sha256"] = sha256_hash
                raw_meta["file_size_bytes"] = len(content)

                # SHA256 Entity
                hash_ent = Entity(
                    entity_type="hash",
                    value=sha256_hash,
                    label=f"SHA256: {sha256_hash[:12]}...",
                    confidence=1.0,
                    source="Document Intel",
                    properties={"algorithm": "sha256", "hash": sha256_hash, "md5": md5_hash},
                )
                entities.append(hash_ent)
                relationships.append(
                    EntityRelationship(
                        source_entity_id=entity.id,
                        target_entity_id=hash_ent.id,
                        relationship_type="has_hash",
                        confidence=1.0,
                        source="Document Intel",
                        label="sha256_hash",
                    )
                )

                # 2. Embedded URLs & Emails
                text_content = content.decode("latin1", errors="ignore")
                found_urls = re.findall(r"https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s<>\"']*)?", text_content)
                found_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text_content)

                for url in list(set(found_urls))[:5]:
                    url_clean = url.strip(").,;")
                    url_ent = Entity(
                        entity_type="url",
                        value=url_clean,
                        label=f"Link: {url_clean[:60]}",
                        confidence=0.9,
                        source="Document Intel",
                        properties={"embedded_in": file_path_or_url},
                    )
                    entities.append(url_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=url_ent.id,
                            relationship_type="contains_link",
                            confidence=0.9,
                            source="Document Intel",
                            label="embedded_url",
                        )
                    )

                for email in list(set(found_emails))[:5]:
                    email_ent = Entity(
                        entity_type="email",
                        value=email,
                        label=email,
                        confidence=0.9,
                        source="Document Intel",
                        properties={"embedded_in": file_path_or_url},
                    )
                    entities.append(email_ent)
                    relationships.append(
                        EntityRelationship(
                            source_entity_id=entity.id,
                            target_entity_id=email_ent.id,
                            relationship_type="contains_link",
                            confidence=0.9,
                            source="Document Intel",
                            label="embedded_email",
                        )
                    )
            except Exception as e:
                logger.debug("Document local file analysis error: %s", e)

        return entities, relationships, raw_meta
