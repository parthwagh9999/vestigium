import asyncio
import json
import logging
from typing import Any

from app.transforms.base import BaseTransform
from app.models.entity import Entity
from app.models.relationship import EntityRelationship

logger = logging.getLogger(__name__)


class ExifToolAdapter(BaseTransform):
    id = "kali.exiftool"
    name = "ExifTool (Metadata Extraction)"
    description = "Extracts metadata from documents and images."
    category = "Document Intelligence"
    
    input_entity_types = ["document", "image", "url"]
    output_entity_types = ["person", "location", "software", "camera"]
    
    is_passive = True
    requires_api_key = False
    supported_os = ["linux", "darwin", "windows"]
    
    import shutil
    install_status = "installed" if shutil.which("exiftool") else "not_installed"

    async def execute(
        self,
        entity: Entity,
        params: dict[str, Any]
    ) -> tuple[list[Entity], list[EntityRelationship], dict[str, Any]]:
        
        if self.install_status != "installed":
            # Graceful degradation
            return [], [], {"error": "ExifTool is not installed"}

        # In a real environment, we'd need to download the URL to a temp file,
        # or if the entity is a local file, just read it.
        # For this prototype, we'll assume the entity value is a URL and try to fetch it 
        # or it's a file path.
        
        target = entity.value
        
        import os
        import urllib.request
        import tempfile
        
        temp_path = None
        if target.startswith("http"):
            # Download it to temp
            fd, temp_path = tempfile.mkstemp()
            os.close(fd)
            try:
                urllib.request.urlretrieve(target, temp_path)
                file_to_scan = temp_path
            except Exception as e:
                if temp_path:
                    os.unlink(temp_path)
                raise RuntimeError(f"Failed to download {target} for ExifTool: {e}")
        else:
            file_to_scan = target
            
        if not os.path.exists(file_to_scan):
            if temp_path:
                os.unlink(temp_path)
            raise RuntimeError(f"File not found: {file_to_scan}")
            
        cmd = ["exiftool", "-j", file_to_scan]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and not stdout:
                logger.error(f"ExifTool failed: {stderr.decode()}")
                raise RuntimeError(f"ExifTool execution failed: {stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Failed to run ExifTool: {e}")
            raise RuntimeError(f"Failed to run ExifTool: {e}")
        finally:
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)

        # Parse output
        output_text = stdout.decode('utf-8')
        
        entities = []
        relationships = []
        
        try:
            data = json.loads(output_text)
            if data and len(data) > 0:
                metadata = data[0]
                
                # Extract some common fields
                author = metadata.get("Author") or metadata.get("Creator")
                software = metadata.get("Software") or metadata.get("CreatorTool")
                gps = metadata.get("GPSPosition")
                
                if author:
                    e = Entity(entity_type="person", value=author, label=author, confidence=0.8, source="ExifTool")
                    entities.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="created_by", confidence=0.8, source="ExifTool"))
                    
                if software:
                    e = Entity(entity_type="software", value=software, label=software, confidence=0.9, source="ExifTool")
                    entities.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="uses_software", confidence=0.9, source="ExifTool"))
                    
                if gps:
                    e = Entity(entity_type="location", value=gps, label=gps, confidence=0.9, source="ExifTool")
                    entities.append(e)
                    relationships.append(EntityRelationship(source_entity_id=entity.id, target_entity_id=e.id, relationship_type="located_at", confidence=0.9, source="ExifTool"))
                    
        except json.JSONDecodeError:
            pass
            
        return entities, relationships, {"raw_output": output_text}
