import httpx
from typing import Any
import asyncio

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class NessusAdapter(BaseTransform):
    id = "builtin.nessus"
    name = "Tenable Nessus Scanner"
    description = "Triggers an enterprise vulnerability scan via a running Nessus API"
    category = "Active Reconnaissance"
    
    input_entity_types = ["ip_address", "domain"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False
    requires_api_key = True
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
            
        access_key = params.get("api_keys", {}).get("NESSUS_ACCESS_KEY")
        secret_key = params.get("api_keys", {}).get("NESSUS_SECRET_KEY")
        nessus_url = params.get("api_keys", {}).get("NESSUS_URL", "https://localhost:8834")
        policy_uuid = params.get("api_keys", {}).get("NESSUS_POLICY_UUID") # Basic Network Scan UUID
        
        if not access_key or not secret_key:
            return [], [], {"error": "NESSUS_ACCESS_KEY and NESSUS_SECRET_KEY are required."}
            
        headers = {
            "X-ApiKeys": f"accessKey={access_key}; secretKey={secret_key}",
            "Content-Type": "application/json"
        }
        
        try:
            # We must ignore self-signed certs for default Nessus installs
            async with httpx.AsyncClient(verify=False, timeout=30.0, headers=headers) as client:
                
                # 1. Create a Scan
                payload = {
                    "uuid": policy_uuid or "731a8e52-3ea6-a291-ec0a-d2ff0619c19d7bd788d6be818b65", # Default Basic Network Scan
                    "settings": {
                        "name": f"Vestigium Auto-Scan: {target}",
                        "text_targets": target
                    }
                }
                
                resp = await client.post(f"{nessus_url}/scans", json=payload)
                if resp.status_code != 200:
                    return [], [], {"error": f"Failed to create Nessus scan: {resp.text}"}
                    
                scan_id = resp.json().get("scan", {}).get("id")
                
                # 2. Launch the Scan
                launch_resp = await client.post(f"{nessus_url}/scans/{scan_id}/launch")
                if launch_resp.status_code != 200:
                    return [], [], {"error": "Failed to launch Nessus scan."}
                    
                # To prevent blocking the orchestrator for 45 minutes, we return a success 
                # message indicating the scan has been queued in the Enterprise system.
                # In a fully async system, a webhook would catch the completion.
                
                return [], [], {"raw_output": f"Successfully queued Nessus Scan ID {scan_id} for target {target}."}
                
        except httpx.ConnectError:
            return [], [], {"error": f"Could not connect to Nessus daemon at {nessus_url}."}
        except Exception as e:
            return [], [], {"error": str(e)}
