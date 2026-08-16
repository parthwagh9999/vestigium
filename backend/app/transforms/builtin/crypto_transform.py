"""Cryptocurrency wallet transforms for Bitcoin and Ethereum."""
from __future__ import annotations
from typing import Any
import httpx
from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

class BitcoinWalletTransform(BaseTransform):
    """Transform to query Bitcoin address balance, total received, and transaction count using Blockchain.info."""
    id = "builtin.bitcoin_wallet_lookup"
    name = "Bitcoin Wallet Explorer"
    description = "Retrieves BTC balance, total received, and transaction count from Blockchain.info"
    category = "Cryptocurrency"
    
    input_entity_types = ["wallet", "bitcoin_wallet"]
    output_entity_types = ["wallet"]
    
    is_passive = True
    requires_api_key = False
    
    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        btc_address = entity.value.strip()
        url = f"https://blockchain.info/rawaddr/{btc_address}"
        
        entities = []
        relationships = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    return [], [], {"error": f"Blockchain.info returned status code {resp.status_code}"}
                data = resp.json()
                
            final_balance_sats = data.get("final_balance", 0)
            total_received_sats = data.get("total_received", 0)
            n_tx = data.get("n_tx", 0)
            
            btc_balance = final_balance_sats / 1e8
            btc_received = total_received_sats / 1e8
            
            # Update the original node's confidence/source, but here we just return the raw data 
            # Or we can link it to a generic 'wallet' node if they inputted generic wallet.
            
            # Since Maltego usually returns new nodes, we can just return the raw data and let evidence engine capture it.
            
            return entities, relationships, {"raw_data": {
                "balance_btc": btc_balance,
                "total_received_btc": btc_received,
                "total_transactions": n_tx,
            }}
        except Exception as e:
            return [], [], {"error": f"Bitcoin wallet query failed: {e}"}
