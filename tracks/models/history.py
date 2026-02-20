"""
History models for chat conversations.
"""

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class HistoryMessage(BaseModel):
    """Single message in conversation history."""
    
    role: str  # "user" or "assistant"
    content: str  # Main message content
    timestamp: str  # ISO 8601 format
    
    # Full serialized output from Codex (for assistant messages)
    # This includes all tags: meta, user, thinking, agent, exec, file_update, tokens_used, etc.
    serialized_output: Optional[List[dict]] = None  # List of {"tag": str, "data": str}
    
    # Metadata from Codex session (for assistant messages)
    metadata: Optional[dict] = None  # session_id, model, provider, etc.


class HistoryMetadata(BaseModel):
    """Metadata for a conversation."""
    
    session_id: str
    timestamp: str  # ISO 8601 format
    first_message: str  # Preview of first user message
    file_path: str  # Relative path to JSONL file


class HistoryListResponse(BaseModel):
    """Paginated list of conversations."""
    
    conversations: List[HistoryMetadata]
    total: int
    has_more: bool


class HistoryDetailResponse(BaseModel):
    """Full conversation with all messages."""
    
    session_id: str
    messages: List[HistoryMessage]
    created_at: str  # ISO 8601 format
