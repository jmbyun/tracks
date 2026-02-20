#!/usr/bin/env python3
"""
Standalone heartbeat worker script.
Runs as a separate process to avoid blocking the main FastAPI event loop.
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tracks.clients.codex_client import CodexClient
from tracks.clients.gemini_client import GeminiClient
from tracks.services.heartbeat_service import HEARTBEAT_PROMPT
from tracks.config import settings


def run_heartbeat(session_id: str = None, client_type: str = "codex"):
    """
    Execute heartbeat task and return result as JSON.
    
    Args:
        session_id: Optional session ID to resume
        client_type: Type of client to use ("codex" or "gemini")
    """
    print(f"[heartbeat_worker] Starting heartbeat task (client: {client_type})", file=sys.stderr)
    print(f"[heartbeat_worker] Prompt: {HEARTBEAT_PROMPT}", file=sys.stderr)
    
    if client_type == "gemini":
        client = GeminiClient(cwd=settings.AGENT_HOME_PATH)
    else:
        client = CodexClient(cwd=settings.AGENT_HOME_PATH)
    
    cli_output = client.exec_prompt(
        HEARTBEAT_PROMPT,
        session_id=session_id,
        skip_git_repo_check=True,
        allow_edit=True
    )
    
    serialized = client.serialize_output(cli_output)
    
    current_session_id = session_id
    agent_content = []
    serialized_output = []
    metadata = None
    
    for tag, line in serialized:
        serialized_output.append({"tag": tag, "data": line})
        
        if tag == "meta":
            try:
                meta = json.loads(line)
                current_session_id = meta.get("session_id", current_session_id)
                metadata = meta
            except json.JSONDecodeError:
                pass
                
        elif tag == "agent":
            agent_content.append(line)
    
    # Output result as JSON
    result = {
        "session_id": current_session_id,
        "agent_content": agent_content,
        "serialized_output": serialized_output,
        "metadata": metadata
    }
    
    print(json.dumps(result))
    
    assistant_content = "".join(agent_content)
    print(f"[heartbeat_worker] Heartbeat task completed for session: {current_session_id}", file=sys.stderr)
    print(f"[heartbeat_worker] Response:\n{assistant_content[:500]}{'...' if len(assistant_content) > 500 else ''}", file=sys.stderr)


if __name__ == "__main__":
    session_id = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] != "None" else None
    client_type = sys.argv[2] if len(sys.argv) > 2 else "codex"
    
    run_heartbeat(session_id, client_type)
