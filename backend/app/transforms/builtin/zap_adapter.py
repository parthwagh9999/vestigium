import asyncio
import httpx
from typing import Any
import time

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship


class ZapAdapter(BaseTransform):
    id = "builtin.owasp_zap"
    name = "OWASP ZAP Active Scanner"
    description = "Triggers an active vulnerability scan via a running OWASP ZAP API daemon"
    category = "Active Reconnaissance"
    
    input_entity_types = ["url", "domain"]
    output_entity_types = ["vulnerability"]
    
    is_passive = False # Extremely active scanning
    requires_api_key = True # Needs ZAP_API_KEY and ZAP_URL
    
    async def execute(self, entity: Entity, params: dict[str, Any]) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        results = []
        relationships = []
        
        target = entity.value.strip()
        if entity.entity_type == "domain":
            target = f"https://{target}"
            
        api_key = params.get("api_keys", {}).get("ZAP_API_KEY")
        zap_url = params.get("api_keys", {}).get("ZAP_URL", "http://localhost:8080")
        
        if not api_key:
            return [], [], {"error": "ZAP_API_KEY is required."}
            
        headers = {
            "Accept": "application/json",
            "X-ZAP-API-Key": api_key
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=headers) as client:
                # 1. Start Active Scan
                scan_url = f"{zap_url}/JSON/ascan/action/scan/?url={target}&recurse=true"
                resp = await client.get(scan_url)
                
                if resp.status_code != 200:
                    return [], [], {"error": f"Failed to start ZAP scan: {resp.text}"}
                    
                scan_id = resp.json().get("scan")
                if not scan_id:
                    return [], [], {"error": "ZAP did not return a valid scan ID."}
                    
                # We do not want to block the orchestrator for 30 minutes while ZAP runs.
                # In a real enterprise setup, this would be asynchronous and polled later.
                # For this implementation, we will trigger the spider, and then immediately pull existing alerts for the target.
                
                # Fetch Alerts for target
                alerts_url = f"{zap_url}/JSON/core/view/alerts/?baseurl={target}"
                alerts_resp = await client.get(alerts_url)
                
                if alerts_resp.status_code == 200:
                    alerts = alerts_resp.json().get("alerts", [])
                    seen_vulns = set()
                    
                    for alert in alerts:
                        name = alert.get("name")
                        risk = alert.get("risk")
                        
                        if name and risk in ["High", "Medium", "Critical"] and name not in seen_vulns:
                            seen_vulns.add(name)
                            
                            vuln_ent = Entity(
                                entity_type="vulnerability",
                                value=name,
                                label=f"ZAP [{risk}]: {name}",
                                confidence=1.0,
                                source="OWASP ZAP"
                            )
                            vuln_ent.properties = {
                                "risk": risk,
                                "cwe": alert.get("cweid"),
                                "description": alert.get("description", "")
                            }
                            results.append(vuln_ent)
                            relationships.append(
                                EntityRelationship(
                                    source_entity_id=entity.id,
                                    target_entity_id=vuln_ent.id,
                                    relationship_type="vulnerable_to",
                                    confidence=1.0,
                                    source="OWASP ZAP"
                                )
                            )
                            
                return results, relationships, {"raw_output": f"Triggered ZAP Scan {scan_id}. Extracted {len(results)} high/medium alerts."}
                
        except httpx.ConnectError:
            return [], [], {"error": f"Could not connect to ZAP daemon at {zap_url}."}
        except Exception as e:
            return [], [], {"error": str(e)}
