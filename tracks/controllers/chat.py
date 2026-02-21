"""
Chat API endpoints.
"""

import os
import asyncio
import json
from datetime import datetime
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from fastapi import Request

from ..models import ChatRequest
from ..services import history_service
from ..services.heartbeat_service import heartbeat_state
from ..services.client_service import client_state
from ..config import settings


router = APIRouter(prefix="/api", tags=["chat"])


async def chat_stream_generator(req: Request, message: str, session_id: str | None):
    """
    Generate SSE events from Codex CLI streaming output.
    
    Args:
        req: FastAPI Request object for connection state
        message: User message
        session_id: Optional session ID for conversation continuity
        
    Yields:
        SSE events with chat data
    """
    
    # Mark on_demand as active (user is interacting)
    await heartbeat_state.start_on_demand()
    
    client = client_state.get_client(cwd=settings.AGENT_HOME_PATH)
    
    # Save user message to history
    user_timestamp = datetime.now()
    
    # Execute prompt with Codex CLI
    prompt_message = message

    cli_output = client.exec_prompt(
        prompt_message,
        session_id=session_id,
        skip_git_repo_check=True,
        allow_edit=True
    )
    
    # Serialize output
    serialized = client.serialize_output(cli_output)
    
    current_session_id = session_id
    agent_content = []
    serialized_output = []  # Store all serialized output
    metadata = None
    
    try:
        for tag, line in serialized:
            # Check if client disconnected (e.g., clicked Stop)
            if await req.is_disconnected():
                print("[chat] Client disconnected. Aborting generation.", flush=True)
                break
                
            # Store all serialized output
            serialized_output.append({"tag": tag, "data": line})
            
            # Check for usage limits
            switched = client_state.check_and_update_state([{"tag": tag, "data": line}])
            if switched:
                yield {
                    "event": "output",
                    "data": json.dumps({"tag": "error", "data": "Usage limit exceeded. Please start a new chat to use another available agent.\n\n"})
                }
            
            # Stream all output tags
            yield {
                "event": "output",
                "data": json.dumps({"tag": tag, "data": line})
            }
            # Force immediate transmission by yielding control to event loop
            await asyncio.sleep(0)
            
            if tag == "meta":
                # Extract session_id from metadata
                try:
                    meta = json.loads(line)
                    current_session_id = meta.get("session_id", current_session_id)
                    metadata = meta
                    
                    # Save user message now that we have session_id
                    if current_session_id:
                        history_service.save_message(
                            session_id=current_session_id,
                            role="user",
                            content=message,
                            timestamp=user_timestamp
                        )
                    
                    # Send session info to client
                    yield {
                        "event": "session",
                        "data": json.dumps({"session_id": current_session_id})
                    }
                    await asyncio.sleep(0)
                except json.JSONDecodeError:
                    pass
                
            elif tag == "agent":
                # Accumulate agent response for history content
                agent_content.append(line)
                
            elif tag == "done":
                # Save assistant message to history
                assistant_content = "".join(agent_content)
                if current_session_id:
                    history_service.save_message(
                        session_id=current_session_id,
                        role="assistant",
                        content=assistant_content or "Complete",  # Fallback if no agent content
                        serialized_output=serialized_output,
                        metadata=metadata
                    )
                
                # Send completion event
                yield {
                    "event": "done",
                    "data": json.dumps({
                        "session_id": current_session_id,
                        "full_content": assistant_content
                    })
                }
                await asyncio.sleep(0)
    finally:
        # Save assistant message to history if aborted and we have a session
        if await req.is_disconnected() and current_session_id:
            assistant_content = "".join(agent_content)
            if assistant_content:
                history_service.save_message(
                    session_id=current_session_id,
                    role="assistant",
                    content=assistant_content + "\n\n[Stopped by user]",
                    serialized_output=serialized_output,
                    metadata=metadata
                )
        
        # Mark on_demand as complete (starts cooldown timer)
        await heartbeat_state.end_on_demand()


@router.post("/chat")
async def chat(request: ChatRequest, req: Request):
    """
    Chat endpoint with Server-Sent Events streaming.
    
    Args:
        request: Chat request with message and optional session_id
        req: FastAPI Request object
        
    Returns:
        StreamingResponse with SSE events
    """
    return EventSourceResponse(
        chat_stream_generator(req, request.message, request.session_id)
    )
