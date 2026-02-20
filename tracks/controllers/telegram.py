"""
Telegram API endpoints.
"""

from fastapi import APIRouter
from ..services import history_service
from ..models import HistoryListResponse
router = APIRouter(prefix="/api/telegram", tags=["telegram"])

@router.get("/history", response_model=HistoryListResponse)
async def list_telegram_history(
    limit: int = 30,
    offset: int = 0
):
    """
    List Telegram conversation history.
    """
    
    # We use the existing history service but filter for telegram sessions
    # The history service implementation lists all .user.jsonl files
    # We should probably filter in memory for now as history service doesn't support prefix filtering
    
    full_history = history_service.list_conversations(limit=1000, offset=0)
    
    # Filter for sessions starting with "telegram-"
    telegram_conversations = [
        conv for conv in full_history.conversations 
        if conv.session_id.startswith("telegram-")
    ]
    
    # Apply pagination manually
    total = len(telegram_conversations)
    paginated = telegram_conversations[offset:offset + limit]
    has_more = (offset + limit) < total
    
    return HistoryListResponse(
        conversations=paginated,
        total=total,
        has_more=has_more
    )
