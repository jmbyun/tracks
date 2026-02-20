"""
History service for managing heartbeat conversation storage.
Stores logs in heartbeat/ folder instead of history/ folder.
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Optional

from ..models.history import (
    HistoryMessage,
    HistoryMetadata,
    HistoryListResponse,
    HistoryDetailResponse
)
from ..config import settings


def get_heartbeat_file_path(session_id: str, timestamp: datetime) -> str:
    """
    Generate file path for heartbeat JSONL file.
    
    Format: {AGENT_HOME_PATH}/heartbeat/{yyyy}/{mm}/{dd}/{yyyy-mm-ddThh-MM-ss.sss}.{session_id}.heartbeat.jsonl
    
    Args:
        session_id: Codex session ID
        timestamp: Timestamp for the conversation
        
    Returns:
        Absolute path to JSONL file
    """
    # Format timestamp
    ts_str = timestamp.strftime("%Y-%m-%dT%H-%M-%S.%f")[:-3]  # Milliseconds
    
    # Create directory structure
    year = timestamp.strftime("%Y")
    month = timestamp.strftime("%m")
    day = timestamp.strftime("%d")
    
    # Build path - using heartbeat/ instead of history/
    heartbeat_dir = os.path.join(settings.AGENT_HOME_PATH, "heartbeat", year, month, day)
    filename = f"{ts_str}.{session_id}.heartbeat.jsonl"
    
    return os.path.join(heartbeat_dir, filename)


def save_message(
    session_id: str,
    role: str,
    content: str,
    timestamp: Optional[datetime] = None,
    serialized_output: Optional[List[dict]] = None,
    metadata: Optional[dict] = None
) -> str:
    """
    Save a message to heartbeat JSONL file.
    
    Args:
        session_id: Codex session ID
        role: "user" or "assistant"
        content: Message content
        timestamp: Message timestamp (defaults to now)
        serialized_output: Full serialized output from Codex (for assistant messages)
        metadata: Metadata from Codex session (for assistant messages)
        
    Returns:
        Path to the JSONL file
    """
    if timestamp is None:
        timestamp = datetime.now()
    
    # Find existing file for this session or create new one
    heartbeat_dir = os.path.join(settings.AGENT_HOME_PATH, "heartbeat")
    file_path = None
    
    # Search for existing file with this session_id
    if os.path.exists(heartbeat_dir):
        for root, dirs, files in os.walk(heartbeat_dir):
            for filename in files:
                if session_id in filename and filename.endswith('.heartbeat.jsonl'):
                    file_path = os.path.join(root, filename)
                    break
            if file_path:
                break
    
    # If no existing file, create new one with current timestamp
    if not file_path:
        file_path = get_heartbeat_file_path(session_id, timestamp)
        # Ensure directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create message object
    message = HistoryMessage(
        role=role,
        content=content,
        timestamp=timestamp.isoformat(),
        serialized_output=serialized_output,
        metadata=metadata
    )
    
    # Append to JSONL file
    with open(file_path, 'a', encoding='utf-8') as f:
        f.write(message.model_dump_json() + '\n')
    
    return file_path


def list_conversations(
    limit: int = 30,
    offset: int = 0
) -> HistoryListResponse:
    """
    List heartbeat conversations with pagination.
    
    Args:
        limit: Maximum number of conversations to return
        offset: Number of conversations to skip
        
    Returns:
        HistoryListResponse with conversation metadata
    """
    heartbeat_dir = os.path.join(settings.AGENT_HOME_PATH, "heartbeat")
    
    if not os.path.exists(heartbeat_dir):
        return HistoryListResponse(conversations=[], total=0, has_more=False)
    
    # Find all JSONL files and group by session_id
    conversations_dict = {}  # session_id -> HistoryMetadata
    
    for root, dirs, files in os.walk(heartbeat_dir):
        for filename in files:
            if filename.endswith('.heartbeat.jsonl'):
                file_path = os.path.join(root, filename)
                
                try:
                    # Parse filename: {timestamp}.{session_id}.heartbeat.jsonl
                    parts = filename.rsplit('.', 3)
                    if len(parts) >= 3:
                        timestamp_str = parts[0]
                        session_id = parts[1]
                        
                        # Skip if we already have this session
                        if session_id in conversations_dict:
                            continue
                        
                        # Read first message for preview
                        first_message = ''
                        with open(file_path, 'r', encoding='utf-8') as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    msg = json.loads(line)
                                    first_message = msg.get('content', '')[:100]
                                    break
                        
                        # Parse timestamp
                        if 'T' in timestamp_str:
                            date_part, time_part = timestamp_str.split('T')
                            time_part = time_part.replace('-', ':')
                            timestamp_iso = f"{date_part}T{time_part}"
                        else:
                            timestamp_iso = timestamp_str
                        
                        # Convert to KST (UTC+9)
                        try:
                            dt = datetime.fromisoformat(timestamp_iso)
                            dt_kst = dt + timedelta(hours=9)
                            timestamp_iso = dt_kst.isoformat()
                        except ValueError:
                            pass
                        
                        # Get relative path
                        rel_path = os.path.relpath(file_path, settings.AGENT_HOME_PATH)
                        
                        conversations_dict[session_id] = HistoryMetadata(
                            session_id=session_id,
                            timestamp=timestamp_iso,
                            first_message=first_message,
                            file_path=rel_path
                        )
                except Exception as e:
                    print(f"Error parsing heartbeat file {filename}: {e}")
                    continue
    
    # Convert to list
    conversations = list(conversations_dict.values())
    
    # Sort by timestamp descending
    conversations.sort(key=lambda x: x.timestamp, reverse=True)
    
    # Apply pagination
    total = len(conversations)
    paginated = conversations[offset:offset + limit]
    has_more = (offset + limit) < total
    
    return HistoryListResponse(
        conversations=paginated,
        total=total,
        has_more=has_more
    )


def get_conversation(session_id: str) -> Optional[HistoryDetailResponse]:
    """
    Load full heartbeat conversation by session ID.
    
    Args:
        session_id: Codex session ID
        
    Returns:
        HistoryDetailResponse with all messages, or None if not found
    """
    heartbeat_dir = os.path.join(settings.AGENT_HOME_PATH, "heartbeat")
    
    if not os.path.exists(heartbeat_dir):
        return None
    
    # Find file with matching session_id
    for root, dirs, files in os.walk(heartbeat_dir):
        for filename in files:
            if session_id in filename and filename.endswith('.heartbeat.jsonl'):
                file_path = os.path.join(root, filename)
                
                try:
                    # Parse filename for timestamp
                    parts = filename.rsplit('.', 3)
                    timestamp_str = parts[0]
                    
                    # Parse timestamp
                    if 'T' in timestamp_str:
                        date_part, time_part = timestamp_str.split('T')
                        time_part = time_part.replace('-', ':')
                        timestamp_iso = f"{date_part}T{time_part}"
                    else:
                        timestamp_iso = timestamp_str
                    
                    # Convert to KST (UTC+9)
                    try:
                        dt = datetime.fromisoformat(timestamp_iso)
                        dt_kst = dt + timedelta(hours=9)
                        timestamp_iso = dt_kst.isoformat()
                    except ValueError:
                        pass
                    
                    # Read all messages
                    messages = []
                    with open(file_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                msg_data = json.loads(line)
                                messages.append(HistoryMessage(**msg_data))
                    
                    return HistoryDetailResponse(
                        session_id=session_id,
                        messages=messages,
                        created_at=timestamp_iso
                    )
                except Exception as e:
                    print(f"Error loading heartbeat conversation {session_id}: {e}")
                    return None
    
    return None
