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


class ClientState:
    """
    Singleton class to manage the active client type.
    """
    _instance: Optional['ClientState'] = None
    
    CLIENT_CODEX = "codex"
    CLIENT_GEMINI = "gemini"
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self._client_type = self.CLIENT_CODEX
        print(f"[client_service] Initialized with client: {self._client_type}")
        
    @property
    def client_type(self) -> str:
        return self._client_type
        
    def set_client_type(self, client_type: str):
        if client_type not in (self.CLIENT_CODEX, self.CLIENT_GEMINI):
            raise ValueError(f"Invalid client type: {client_type}")
            
        if self._client_type != client_type:
            print(f"[client_service] Switching client from {self._client_type} to {client_type}")
            self._client_type = client_type
            
    def get_client(self, cwd: Optional[str] = None) -> Union[CodexClient, GeminiClient]:
        """Get the currently active client instance."""
        if self._client_type == self.CLIENT_GEMINI:
            return GeminiClient(cwd=cwd)
        else:
            return CodexClient(cwd=cwd)
            
    def check_and_update_state(self, serialized_output: List[Dict[str, Any]]):
        """
        Check output for usage limit errors and switch client if needed.
        
        Args:
            serialized_output: List of output events [{'tag': '...', 'data': '...'}]
        """
        # Check if we are using codex
        if self._client_type == self.CLIENT_CODEX:
            for event in serialized_output:
                if event.get("tag") == "user":
                    data = event.get("data", "")
                    # Check for usage limit error pattern
                    if "ERROR: You've hit your usage limit" in data:
                        print(f"[client_service] Detected usage limit error. Switching to Gemini.")
                        self.set_client_type(self.CLIENT_GEMINI)
                        return
                        
        # Check if we are using gemini
        elif self._client_type == self.CLIENT_GEMINI:
            for event in serialized_output:
                # Check stderr or error tags for capacity message
                if event.get("tag") in ("stderr", "error"):
                    data = event.get("data", "")
                    if "exhausted" in data and "capacity" in data:
                        print(f"[client_service] Detected Gemini capacity exhaustion. Switching back to Codex.")
                        self.set_client_type(self.CLIENT_CODEX)
                        return


# Singleton instance
client_state = ClientState()
