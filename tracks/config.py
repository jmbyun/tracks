import os
import json
from typing import Dict, Any

from pydantic_settings import BaseSettings


def from_root(path: str):
    return os.path.normpath(os.path.join(os.path.abspath(__file__), "../../", path))


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server configuration
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = 8540
    API_KEY: str = "tracks!"
    
    # Logging
    LOG_LEVEL: str = "INFO"

    # Path settings
    AGENT_HOME_PATH: str = from_root("agent")
    STORAGE_PATH: str = from_root("storage")
    VAULT_PATH: str = from_root("vault.json")

    # Heartbeat settings
    HEARTBEAT_COOLDOWN_SECONDS: int = 600
    ON_DEMAND_COOLDOWN_SECONDS: int = 600

    # Standard message integration settings
    ENABLE_TELEGRAM: bool = False

    # Standard agent integration settings
    AGENT_USE_ORDER: str = "codex,gemini"
    
    # Timezone settings
    UTC_OFFSET: int = 9
    
    class Config:
        env_prefix = "TRACKS_"
        case_sensitive = True


def get_settings() -> Settings:
    """
    Load settings, overriding defaults with values from config.json if it exists.
    """
    config_path = from_root("config.json")
    
    config_overrides: Dict[str, Any] = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    config_overrides = json.loads(content)
        except Exception as e:
            # Proceed with defaults if config loading fails
            print(f"Warning: Failed to load config.json: {e}")
            pass
            
    return Settings(**config_overrides)


class SettingsProxy:
    """Proxy to reload settings from config.json on every access."""
    def __getattr__(self, name: str) -> Any:
        return getattr(get_settings(), name)

settings = SettingsProxy()
