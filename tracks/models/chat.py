"""
Chat-related Pydantic models.
"""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    message: str
    session_id: str | None = None


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    message: str
    session_id: str


class SessionInfo(BaseModel):
    """Session metadata."""
    
    session_id: str
