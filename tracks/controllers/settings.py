import os
import json
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..config import settings
from ..services.client_service import client_state

router = APIRouter(prefix="/api/settings", tags=["settings"])

# Calculate config.json path from this file
# tracks/controllers/settings.py -> tracks/config.json is one level up, then config.json
# Actually based on tracks/config.py, it's in the project root.
# tracks/controllers/settings.py -> project_root/config.json is ../../config.json
CONFIG_PATH = os.path.normpath(os.path.join(os.path.abspath(__file__), "../../../config.json"))
VAULT_PATH = settings.VAULT_PATH

class ConfigUpdate(BaseModel):
    HEARTBEAT_COOLDOWN_SECONDS: int = None
    ON_DEMAND_COOLDOWN_SECONDS: int = None
    ENABLE_TELEGRAM: bool = None
    AGENT_USE_ORDER: str = None
    UTC_OFFSET: int = None

class VaultItem(BaseModel):
    key: str
    value: str

class ActiveClientUpdate(BaseModel):
    client_type: str

def read_json_file(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                return {}
            return json.loads(content)
    except Exception as e:
        print(f"Error reading {path}: {e}")
        return {}

def write_json_file(path: str, data: Dict[str, Any]):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to write file: {e}")

@router.get("/config")
async def get_config():
    return read_json_file(CONFIG_PATH)

@router.get("/defaults")
async def get_defaults():
    from ..config import Settings
    return Settings().model_dump()


@router.post("/config")
async def update_config(update: ConfigUpdate):
    config = read_json_file(CONFIG_PATH)
    update_data = update.model_dump(exclude_none=True)
    config.update(update_data)
    write_json_file(CONFIG_PATH, config)
    return {"status": "success", "config": config}

@router.get("/active-client")
async def get_active_client():
    from ..config import settings
    available = [c.strip() for c in settings.AGENT_USE_ORDER.split(",") if c.strip()]
    return {
        "active_client": client_state.client_type,
        "available_clients": available
    }

@router.post("/active-client")
async def set_active_client(update: ActiveClientUpdate):
    try:
        client_state.set_client_type(update.client_type)
        return {"status": "success", "active_client": client_state.client_type}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/vault")
async def get_vault():
    vault = read_json_file(VAULT_PATH)
    return [{"key": k, "value": v} for k, v in vault.items()]

@router.post("/vault")
async def create_vault_item(item: VaultItem):
    vault = read_json_file(VAULT_PATH)
    if item.key in vault:
        raise HTTPException(status_code=400, detail="Key already exists")
    vault[item.key] = item.value
    write_json_file(VAULT_PATH, vault)
    return {"status": "success"}

@router.put("/vault/{key}")
async def update_vault_item(key: str, item: VaultItem):
    vault = read_json_file(VAULT_PATH)
    if key not in vault:
        raise HTTPException(status_code=404, detail="Key not found")
    
    # If key is being renamed
    if key != item.key:
        if item.key in vault:
            raise HTTPException(status_code=400, detail="New key already exists")
        del vault[key]
    
    vault[item.key] = item.value
    write_json_file(VAULT_PATH, vault)
    return {"status": "success"}

@router.delete("/vault/{key}")
async def delete_vault_item(key: str):
    vault = read_json_file(VAULT_PATH)
    if key not in vault:
        raise HTTPException(status_code=404, detail="Key not found")
    del vault[key]
    write_json_file(VAULT_PATH, vault)
    return {"status": "success"}
