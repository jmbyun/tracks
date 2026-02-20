#!/usr/bin/env python3
"""
Standalone cronjob worker script.
Runs as a separate process triggered by cron to execute scheduled tasks.
"""

import sys
import os
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tracks.clients.codex_client import CodexClient
from tracks.clients.gemini_client import GeminiClient
from tracks.config import settings
from tracks.services.client_service import client_state
from tracks.vault import vault
import requests

def send_telegram_error(prompt_text: str):
    bot_token = vault.get("TELEGRAM_BOT_TOKEN")
    user_ids = vault.get("TELEGRAM_USER_IDS")
    
    if not bot_token or not user_ids:
        return
        
    user_id_list = [uid.strip() for uid in user_ids.split(",") if uid.strip()]
    if not user_id_list:
        return
        
    for uid in user_id_list:
        try:
            requests.post(
                f"https://api.telegram.org/bot{bot_token}/sendMessage",
                json={
                    "chat_id": uid,
                    "text": f"'{prompt_text}' is failed to ran."
                },
                timeout=5
            )
        except Exception as e:
            print(f"[cronjob_worker] Failed to send Telegram error: {e}", file=sys.stderr)


def run_cronjob(prompt_text: str):
    """
    Execute cronjob task and return result as JSON.
    
    Args:
        prompt_text: The task instructions to execute
    """
    cronjob_prompt = f"[CRONJOB] {prompt_text}"
    
    max_attempts = len(settings.AGENT_USE_ORDER.split(","))
    
    for attempt in range(max_attempts):
        client_type = client_state.client_type
        print(f"[cronjob_worker] Starting cronjob task (attempt {attempt+1}, client: {client_type})", file=sys.stderr)
        print(f"[cronjob_worker] Prompt: {cronjob_prompt}", file=sys.stderr)
        
        if client_type == "gemini":
            client = GeminiClient(cwd=settings.AGENT_HOME_PATH)
        else:
            client = CodexClient(cwd=settings.AGENT_HOME_PATH)
        
        try:
            cli_output = client.exec_prompt(
                cronjob_prompt,
                skip_git_repo_check=True,
                allow_edit=True
            )
            
            serialized = client.serialize_output(cli_output)
            
            current_session_id = None
            agent_content = []
            serialized_output = []
            metadata = None
            
            switched = False
            for tag, line in serialized:
                serialized_output.append({"tag": tag, "data": line})
                if client_state.check_and_update_state([{"tag": tag, "data": line}]):
                    switched = True
                    break
                
                if tag == "meta":
                    try:
                        meta = json.loads(line)
                        current_session_id = meta.get("session_id", current_session_id)
                        metadata = meta
                    except json.JSONDecodeError:
                        pass
                        
                elif tag == "agent":
                    agent_content.append(line)
            
            if switched:
                if attempt < max_attempts - 1:
                    print(f"[cronjob_worker] Client {client_type} limit exhausted, retrying with new client...", file=sys.stderr)
                    continue
                else:
                    print("[cronjob_worker] All clients exhausted.", file=sys.stderr)
                    send_telegram_error(prompt_text)
                    sys.exit(1)
            
            # Output result as JSON
            result = {
                "session_id": current_session_id,
                "agent_content": agent_content,
                "serialized_output": serialized_output,
                "metadata": metadata,
                "success": True
            }
            
            print(json.dumps(result))
            
            assistant_content = "".join(agent_content)
            print(f"[cronjob_worker] Cronjob task completed for session: {current_session_id}", file=sys.stderr)
            print(f"[cronjob_worker] Response:\n{assistant_content[:500]}{'...' if len(assistant_content) > 500 else ''}", file=sys.stderr)
            return
        
        except Exception as e:
            error_msg = f"Failed to execute cronjob: {str(e)}"
            print(f"[cronjob_worker] ERROR: {error_msg}", file=sys.stderr)
            if attempt == max_attempts - 1:
                result = {
                    "success": False,
                    "error": error_msg
                }
                print(json.dumps(result))
                send_telegram_error(prompt_text)
                sys.exit(1)
            else:
                client_state.set_client_type(client_state.get_next_client_type())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cronjob_worker.py <prompt_text>")
        sys.exit(1)
        
    prompt_text = sys.argv[1]
    
    run_cronjob(prompt_text)
