from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
import os
from datetime import datetime

from ..config import settings

router = APIRouter(
    prefix="/api/browser",
    tags=["browser"]
)


def get_safe_path(base_path: str, req_path: str) -> str:
    """Ensure the requested path is within the base path."""
    # Normalize to prevent trickery like ../../
    normalized_path = os.path.normpath(os.path.join(base_path, req_path.lstrip("/")))
    if not normalized_path.startswith(os.path.abspath(base_path)):
        raise HTTPException(status_code=403, detail="Access denied")
    return normalized_path

@router.get("/list")
async def list_files(path: str = Query("")):
    """List files in a directory."""
    base_path = settings.AGENT_HOME_PATH
    target_path = get_safe_path(base_path, path)
    
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="Directory not found")
        
    if not os.path.isdir(target_path):
        raise HTTPException(status_code=400, detail="Not a directory")
        
    try:
        items = []
        for entry in os.scandir(target_path):
            stat_info = entry.stat()
            items.append({
                "id": entry.name,
                "name": entry.name,
                "isDir": entry.is_dir(),
                "size": stat_info.st_size if entry.is_file() else 0,
                "modDate": datetime.fromtimestamp(stat_info.st_mtime).isoformat()
            })
        
        # Sort directories first, then alphabetically
        items.sort(key=lambda x: (not x["isDir"], x["name"].lower()))
        return items
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/file")
async def get_file(path: str = Query(...)):
    """Download a file."""
    base_path = settings.AGENT_HOME_PATH
    target_path = get_safe_path(base_path, path)
    
    if not os.path.exists(target_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    if not os.path.isfile(target_path):
        raise HTTPException(status_code=400, detail="Not a file")
        
    return FileResponse(target_path)
