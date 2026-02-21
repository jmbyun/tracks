import os
import json
import secrets
import string
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


def generate_random_api_key(length=12):
    """Generate a random alphanumeric string."""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


    return config_overrides


def get_settings() -> Settings:
    """
    Load settings, overriding defaults with values from config.json if it exists.
    If the API_KEY is the default "tracks!", it is replaced with a random one and saved.
    """
    config_path = from_root("config.json")
    config_overrides = _load_config(config_path)
    
    settings = Settings(**config_overrides)
    
    if settings.API_KEY == "tracks!":
        new_key = generate_random_api_key()
        print(f"[config] Security: Replacing default API_KEY with random one.")
        config_overrides["API_KEY"] = new_key
        
        # Save back to config.json
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config_overrides, f, indent=4)
            print(f"[config] Updated {config_path} with new API_KEY.")
        except Exception as e:
            print(f"Warning: Failed to save updated API_KEY to config.json: {e}")
            
        settings = Settings(**config_overrides)
            
    return settings


def _load_config(config_path: str) -> Dict[str, Any]:
    """Helper to load config from JSON file."""
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    return json.loads(content)
        except Exception as e:
            print(f"Warning: Failed to load config.json: {e}")
    return {}


class SettingsProxy:
    """Proxy to reload settings from config.json on every access."""
    def __getattr__(self, name: str) -> Any:
        return getattr(get_settings(), name)

settings = SettingsProxy()
