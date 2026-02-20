"""
Heartbeat runner - executes background LLM tasks.
"""

import json
import asyncio
import subprocess
import sys
import os
from datetime import datetime
from typing import Optional

from . import heartbeat_history_service
from .heartbeat_service import heartbeat_state, HEARTBEAT_PROMPT
from .client_service import client_state


async def run_heartbeat_task():
    """
    Execute a single heartbeat task iteration.
    
    This function:
    1. Checks if a new session should be created (date changed)
    2. Spawns a separate subprocess to run Codex CLI
    3. Saves the response to heartbeat history
    4. Updates the heartbeat state
    """
    print(f"[heartbeat_runner] Starting heartbeat task")
    print(f"[heartbeat_runner] Prompt: {HEARTBEAT_PROMPT}")
    
    # Mark heartbeat as active
    await heartbeat_state.start_heartbeat()
    
    try:
        # Check if we need a new session
        session_id = None
        if not heartbeat_state.should_create_new_session():
            session_id = heartbeat_state.heartbeat_session_id
            print(f"[heartbeat_runner] Resuming session: {session_id}")
        else:
            print(f"[heartbeat_runner] Creating new session (date changed or first run)")
        
        # Save user message timestamp
        user_timestamp = datetime.now()
        
        # Get path to worker script
        worker_path = os.path.join(os.path.dirname(__file__), "heartbeat_worker.py")
        
        # Build command
        cmd = [sys.executable, worker_path]
        if session_id:
            cmd.append(session_id)
        else:
            cmd.append("None")
            
        # Add client type
        cmd.append(client_state.client_type)
        
        # Run worker as subprocess (non-blocking)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        # Print worker stderr (logs) to main process
        if stderr:
            print(stderr.decode('utf-8', errors='replace'), end='')
        
        # Parse worker stdout (JSON result)
        if stdout:
            stdout_text = stdout.decode('utf-8', errors='replace')
            
            # Find the JSON object in stdout (skip any CLI warning lines)
            json_start = stdout_text.find('{')
            if json_start >= 0:
                json_text = stdout_text[json_start:]
                try:
                    result = json.loads(json_text)
                    current_session_id = result.get("session_id")
                    agent_content = result.get("agent_content", [])
                    serialized_output = result.get("serialized_output", [])
                    metadata = result.get("metadata")
                    
                    # Check for usage limits
                    client_state.check_and_update_state(serialized_output)
                    
                    # Update heartbeat session id
                    if current_session_id:
                        heartbeat_state.set_heartbeat_session_id(current_session_id)
                        
                        # Save user message
                        heartbeat_history_service.save_message(
                            session_id=current_session_id,
                            role="user",
                            content=HEARTBEAT_PROMPT,
                            timestamp=user_timestamp
                        )
                        
                        # Save assistant message
                        assistant_content = "".join(agent_content)
                        heartbeat_history_service.save_message(
                            session_id=current_session_id,
                            role="assistant",
                            content=assistant_content or "Complete",
                            serialized_output=serialized_output,
                            metadata=metadata
                        )
                        
                        print(f"[heartbeat_runner] Saved to history for session: {current_session_id}")
                except json.JSONDecodeError as e:
                    print(f"[heartbeat_runner] Failed to parse worker output: {e}")
                    print(f"[heartbeat_runner] Raw output: {stdout_text[:500]}")
            else:
                print(f"[heartbeat_runner] No JSON found in worker output")
                print(f"[heartbeat_runner] Raw output: {stdout_text[:500]}")
        
    except Exception as e:
        print(f"[heartbeat_runner] Error running heartbeat task: {e}")
    
    finally:
        # Mark heartbeat as complete (starts cooldown timer)
        await heartbeat_state.end_heartbeat()


async def trigger_heartbeat_task():
    """
    Callback function to trigger heartbeat task.
    This is called when both flags become False.
    """
    from .heartbeat_service import heartbeat_state
    await run_heartbeat_task()

