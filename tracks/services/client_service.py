"""
Service for managing the active LLM client (Codex or Gemini).
Handles automatic switching when usage limits are hit.
"""

from typing import Optional, Union, Any, Dict, List
import json
import os
import sys

from tracks.clients.codex_client import CodexClient
from tracks.clients.gemini_client import GeminiClient
from tracks.config import settings


class ClientState:
    """
    Singleton class to manage the active client type.
    """
    _instance: Optional['ClientState'] = None
    
    CLIENT_TYPES = ["codex", "gemini"]
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._client_type = settings.AGENT_USE_ORDER.split(",")[0]
        print(f"[client_service] Initialized with client: {self._client_type}")
        
    @property
    def client_type(self) -> str:
        return self._client_type
        
    def set_client_type(self, client_type: str):
        if client_type.split(":", 1)[0] not in self.CLIENT_TYPES:
            raise ValueError(f"Invalid client type: {client_type}")
            
        if self._client_type != client_type:
            print(f"[client_service] Switching client from {self._client_type} to {client_type}")
            self._client_type = client_type
            
    def get_client(self, cwd: Optional[str] = None) -> Union[CodexClient, GeminiClient]:
        """Get the currently active client instance."""
        if ":" not in self._client_type:
            profile_id = "main"
        else:
            profile_id = self._client_type.split(":", 1)[1]
        which_client = self._client_type.split(":", 1)[0]
        
        if which_client == "gemini":
            return GeminiClient(cwd=cwd, profile_id=profile_id)
        elif which_client == "codex":
            return CodexClient(cwd=cwd, profile_id=profile_id)
        else:
            raise ValueError(f"Invalid client type: {self._client_type}")

    def get_next_client_type(self):
        """Get the next client type in the order."""
        client_types_order = settings.AGENT_USE_ORDER.split(",")
        current_index = client_types_order.index(self._client_type)
        next_index = (current_index + 1) % len(client_types_order)
        return client_types_order[next_index]
            
    def check_and_update_state(self, serialized_output: List[Dict[str, Any]]):
        """
        Check output for usage limit errors and switch client if needed.
        
        Args:
            serialized_output: List of output events [{'tag': '...', 'data': '...'}]
        """
        next_client_type = self.get_next_client_type()

        # Check if we are using codex
        if self._client_type == "codex":
            for event in serialized_output:
                if event.get("tag") == "user":
                    data = event.get("data", "")
                    # Check for usage limit error pattern
                    if "ERROR: You've hit your usage limit" in data: 
                        print(f"[client_service] Detected Codex usage limit exhaustion. Switching to {next_client_type.capitalize()}.")
                        self.set_client_type(next_client_type)
                        return True
                        
        # Check if we are using gemini
        elif self._client_type == "gemini":
            for event in serialized_output:
                # Check stderr or error tags for capacity message
                if event.get("tag") in ("stderr", "error"):
                    data = event.get("data", "")
                    if "exhausted" in data and "capacity" in data:
                        print(f"[client_service] Detected Gemini usage limit exhaustion. Switching to {next_client_type.capitalize()}.")
                        self.set_client_type(next_client_type)
                        return True
        return False


# Singleton instance
client_state = ClientState()
