"""
Heartbeat API endpoints.
"""

import os
from fastapi import APIRouter, Query

from ..services.heartbeat_service import heartbeat_state
from ..services import heartbeat_history_service


router = APIRouter(prefix="/api/heartbeat", tags=["heartbeat"])


@router.get("/status")
async def get_status():
    """
    Get current heartbeat system status.
    
    Returns:
        dict with current flag states and configuration
    """
    return heartbeat_state.get_status()


@router.get("/history")
async def list_heartbeat_sessions(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List heartbeat sessions with pagination.
    
    Args:
        limit: Maximum number of sessions to return (1-100)
        offset: Number of sessions to skip
        
    Returns:
        HistoryListResponse with session metadata
    """
    return heartbeat_history_service.list_conversations(limit, offset)


@router.get("/history/{session_id}")
async def get_heartbeat_session(session_id: str):
    """
    Get a specific heartbeat session's messages.
    
    Args:
        session_id: UUID of the session
        
    Returns:
        ConversationResponse with messages
    """
    return heartbeat_history_service.get_conversation(session_id)

