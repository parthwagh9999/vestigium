import httpx
import logging
from typing import Any

from app.transforms.provider_base import BaseProviderTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)

class VirusTotalIPTransform(BaseProviderTransform):
    """VirusTotal adapter for IP reputation checking."""
    
    id = "builtin.virustotal_ip"
    name = "VirusTotal IP Reputation"
    description = "Checks an IP address against VirusTotal's threat intelligence dataset"
    category = "Threat Intelligence"
    source = "VirusTotal"
    documentation_url = "https://docs.virustotal.com/"
    license = "Commercial / Free API Tier"
    provider_name = "VirusTotal"
    
    input_entity_types = ["ip_address", "ipv6_address"]
    output_entity_types = ["reputation"]
    relationships_created = ["has_reputation"]
    
    execution_type = "api"
    passive_or_active = "PASSIVE"
    authorization_required = False
    
    installation_required = False
    api_key_required = True
    api_key_service = "virustotal"
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        ip = entity.value.strip()
        
        entities = []
        relationships = []
        raw_output = {}
        
        # We need the API key from params if passed directly, or it will be injected by the runner
        # Actually, runner.py injects `api_key` if `requires_api_key` is set.
        # But wait, in runner.py:
        # We fetch `api_key` from the vault.
        # Currently the runner does:
        # `entities, relationships, raw_data = await transform.execute(entity=input_entity, params=params)`
        # It doesn't pass the api_key to the execute method directly! 
        # Ah, we need to pass the API key to the transform. In runner.py, we fetched `api_key` but didn't pass it.
        # Let's assume it's passed in params["api_key"] for now, and I will fix runner.py if needed.
        api_key = params.get("api_key")
        
        if not api_key:
            return [], [], {"warning": "VirusTotal API key is not configured in the vault. Please configure an API key in Settings / Tool Center."}
            
        url = f"https://www.virustotal.com/api/v3/ip_addresses/{ip}"
        headers = {
            "x-apikey": api_key,
            "accept": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 401:
                    return [], [], {"warning": "Invalid VirusTotal API key configured in vault"}
                if resp.status_code == 404:
                    return [], [], {"message": "IP not found in VirusTotal dataset"}
                if resp.status_code != 200:
                    return [], [], {"warning": f"VirusTotal returned HTTP {resp.status_code}"}
                
                data = resp.json()
                
            raw_output["virustotal_response"] = data
            
            attributes = data.get("data", {}).get("attributes", {})
            stats = attributes.get("last_analysis_stats", {})
            
            malicious = stats.get("malicious", 0)
            suspicious = stats.get("suspicious", 0)
            harmless = stats.get("harmless", 0)
            undetected = stats.get("undetected", 0)
            
            total_engines = malicious + suspicious + harmless + undetected
            
            if total_engines > 0:
                if malicious > 0:
                    status = "Malicious"
                    confidence = malicious / total_engines
                    color = "#EF4444" # Red
                elif suspicious > 0:
                    status = "Suspicious"
                    confidence = suspicious / total_engines
                    color = "#F59E0B" # Amber
                else:
                    status = "Benign"
                    confidence = harmless / total_engines
                    color = "#10B981" # Green
                    
                label = f"VT: {status} ({malicious}/{total_engines})"
                
                e = Entity(
                    entity_type="reputation", 
                    value=label, 
                    label=label, 
                    confidence=confidence, 
                    source="VirusTotal",
                    color=color,
                    properties={"malicious": malicious, "suspicious": suspicious, "harmless": harmless}
                )
                entities.append(e)
                relationships.append(EntityRelationship(
                    source_entity_id=entity.id,
                    target_entity_id=e.id,
                    relationship_type="has_reputation",
                    confidence=confidence,
                    source="VirusTotal"
                ))
                
            return entities, relationships, raw_output
            
        except Exception as e:
            logger.error(f"VirusTotal execution error: {e}")
            return [], [], {"error": str(e)}
