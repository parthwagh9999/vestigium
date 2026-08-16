import asyncio
import logging
import shutil
from typing import Dict, Any

from app.transforms.registry import transform_registry

logger = logging.getLogger(__name__)

class ToolHealthService:
    """Service to automatically check the health and availability of OSINT tools on startup."""

    @classmethod
    async def run_startup_checks(cls) -> None:
        """Run health checks on all registered transforms and update their availability status."""
        logger.info("Running OSINT Tool ecosystem health checks...")
        
        transforms = transform_registry.list_all()
        for transform in transforms:
            try:
                await cls._check_transform(transform)
            except Exception as e:
                logger.error(f"Error checking health for transform {transform.name}: {e}")
                transform.availability_status = "FAILED_HEALTH_CHECK"
        
        logger.info("Tool health checks completed.")

    @classmethod
    async def _check_transform(cls, transform: Any) -> None:
        """Check a single transform."""
        
        # 1. API Key Requirement Check
        if transform.api_key_required or transform.requires_api_key:
            # We'll set this to CONFIGURATION_REQUIRED initially.
            # When the user adds a key, it should switch to AVAILABLE_WITH_API_KEY.
            transform.availability_status = "CONFIGURATION_REQUIRED"
            transform.configuration_status = "NOT_CONFIGURED"
            
        # 2. Binary Installation Check
        elif getattr(transform, 'installation_required', False):
            binary_name = cls._get_binary_name(transform.id)
            if binary_name:
                if shutil.which(binary_name):
                    transform.availability_status = "AVAILABLE"
                    transform.install_status = "installed"
                else:
                    transform.availability_status = "NOT_INSTALLED"
                    transform.install_status = "not_installed"
            else:
                transform.availability_status = "AVAILABLE"

        # 3. Default passive/local tools
        else:
            transform.availability_status = "AVAILABLE"

    @classmethod
    def _get_binary_name(cls, transform_id: str) -> str | None:
        """Map a transform ID to its underlying binary executable."""
        mapping = {
            "kali.theharvester": "theHarvester",
            "kali.sherlock": "sherlock",
            "kali.amass": "amass",
            "kali.exiftool": "exiftool",
            "builtin.nmap": "nmap",
            "builtin.subfinder": "subfinder",
            "builtin.httpx": "httpx",
            "builtin.findomain": "findomain",
            "builtin.assetfinder": "assetfinder",
            "builtin.whatweb": "whatweb",
            "builtin.wafw00f": "wafw00f",
            "builtin.maigret": "maigret",
            "builtin.gitleaks": "gitleaks",
        }
        return mapping.get(transform_id)
