"""
History API endpoints.
"""

import os
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..services import history_service
from ..models import HistoryListResponse, HistoryDetailResponse
from ..config import settings

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("", response_model=HistoryListResponse)
async def list_conversations(
    limit: int = Query(30, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List conversations with pagination.
    
    Args:
        limit: Maximum number of conversations to return (1-100)
        offset: Number of conversations to skip
        
    Returns:
        HistoryListResponse with conversation metadata
    """
    # Exclude Telegram conversations from the main history list
    return history_service.list_conversations(limit, offset, exclude_prefix="telegram-")


@router.get("/{session_id}", response_model=HistoryDetailResponse)
async def get_conversation(session_id: str):
    """
    Get full conversation by session ID.
    
    Args:
        session_id: Codex session ID
        
    Returns:
        HistoryDetailResponse with all messages
    """
    conversation = history_service.get_conversation(session_id)
    
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversation
