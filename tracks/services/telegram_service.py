"""
Telegram polling service for Tracks.
"""

import asyncio
import logging
import requests
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

from ..config import settings
from ..vault import vault
from ..services.heartbeat_service import heartbeat_state
from ..services.client_service import client_state
from ..services import history_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TelegramService:
    """
    Singleton service to handle Telegram polling and message processing.
    """
    _instance: Optional['TelegramService'] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self.bot_token = None
        self.base_url = None
        self.allowed_user_ids = []
        self.offset = 0
        self.is_running = False
        
        # Session management
        # Map telegram_user_id -> current_session_id
        self.user_sessions: Dict[str, str] = {}
        # Map session_id -> message_count (user messages only)
        self.session_message_counts: Dict[str, int] = {}

    async def start_polling(self):
        """Start the polling loop."""
        self.is_running = True
        logger.info("[telegram] Starting polling loop...")
        
        while self.is_running:
            # Re-evaluate conditions dynamically
            enable_telegram = getattr(settings, "ENABLE_TELEGRAM", False)
            current_bot_token = vault.get("TELEGRAM_BOT_TOKEN")
            
            if not enable_telegram or not current_bot_token:
                await asyncio.sleep(30)
                continue

            # Load allowed users defensively
            if vault.get("TELEGRAM_USER_IDS"):
                self.allowed_user_ids = [uid.strip() for uid in vault.get("TELEGRAM_USER_IDS").split(",") if uid.strip()]

            # If token changed, update state and regenerate skill file
            if self.bot_token != current_bot_token:
                self.bot_token = current_bot_token
                self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
                self._generate_skill_md()

            try:
                updates = await self._get_updates()
                for update in updates:
                    await self._handle_update(update)
                    self.offset = update["update_id"] + 1
            except Exception as e:
                logger.error(f"[telegram] Polling error: {e}")
                await asyncio.sleep(5) # Wait before retrying
            
            await asyncio.sleep(1)

    def _generate_skill_md(self):
        """Create skills/telegram/SKILL.md in home directory."""
        try:
            telegram_skill_dir = os.path.join(settings.AGENT_HOME_PATH, "skills", "telegram")
            os.makedirs(telegram_skill_dir, exist_ok=True)
            
            telegram_skill_path = os.path.join(telegram_skill_dir, "SKILL.md")
            
            example_user_id = self.allowed_user_ids[0] if self.allowed_user_ids else "USER_ID"
            
            content = f"""---
name: Telegram
description: Send messages to users via Telegram
---

# Telegram Messaging

You can send messages to users via terminal using curl.

## Config
- Bot Token: `{self.bot_token}`
- Allowed Users: `{', '.join(self.allowed_user_ids)}`

## Command
```bash
curl -X POST https://api.telegram.org/bot{self.bot_token}/sendMessage \\
     -H "Content-Type: application/json" \\
     -d '{{"chat_id": "{example_user_id}", "text": "Your message here"}}'
```

## Quick Reference
To send to specific user:
"""
            for uid in self.allowed_user_ids:
                content += f"""
### User {uid}
```bash
curl -X POST https://api.telegram.org/bot{self.bot_token}/sendMessage \\
     -H "Content-Type: application/json" \\
     -d '{{"chat_id": "{uid}", "text": "Hello from Terminal"}}'
```
"""
            
            with open(telegram_skill_path, "w") as f:
                f.write(content)
                
            logger.info(f"[telegram] Created {telegram_skill_path}")
            
        except Exception as e:
            logger.error(f"[telegram] Failed to create skills/telegram/SKILL.md: {e}")

    async def _get_updates(self) -> List[Dict]:
        """Fetch updates from Telegram."""
        # This is a blocking call, so we run it in a thread executor
        loop = asyncio.get_event_loop()
        try:
            return await loop.run_in_executor(None, self._fetch_updates_sync)
        except Exception as e:
            logger.error(f"[telegram] Error fetching updates: {e}")
            return []

    def _fetch_updates_sync(self) -> List[Dict]:
        """Synchronous part of fetching updates."""
        try:
            response = requests.get(
                f"{self.base_url}/getUpdates",
                params={"offset": self.offset, "timeout": 5},
                timeout=7
            )
            response.raise_for_status()
            return response.json().get("result", [])
        except requests.RequestException as e:
            logger.error(f"[telegram] Request error: {e}")
            raise

    async def _handle_update(self, update: Dict):
        """Process a single update."""
        message = update.get("message")
        if not message:
            return

        user = message.get("from")
        if not user:
            return

        user_id = str(user.get("id"))
        text = message.get("text")
        chat_id = message.get("chat", {}).get("id")

        if not text:
            return

        # Access control
        if user_id not in self.allowed_user_ids:
            logger.warning(f"[telegram] Unauthorized access attempt from {user_id}")
            await self._send_message(chat_id, f"Your user ID is {user_id}. Add this user ID to your config.")
            return
        
        # Handle command
        if text.startswith("/"):
            await self._handle_command(chat_id, user_id, text)
            return

        # Process user message
        logger.info(f"[telegram] Received message from {user_id}: {text}")
        await self._process_user_message(chat_id, user_id, text)

    async def _handle_command(self, chat_id, user_id, text):
        """Handle simple commands."""
        if text == "/start":
            await self._send_message(chat_id, "Hello! I am your Tracks bot. Send me a message to start chatting.")
        elif text == "/new":
            # Force new session
            self.user_sessions.pop(user_id, None)
            await self._send_message(chat_id, "Started a new session.")

    async def _process_user_message(self, chat_id, user_id, 
                                    text):
        """Process a valid user message."""
        # 1. Manage Session
        current_session_id = self.user_sessions.get(user_id)
        
        if not current_session_id:
            # Create new session
            current_session_id = self._create_new_session_id(user_id)
            self.user_sessions[user_id] = current_session_id
            self.session_message_counts[current_session_id] = 0
            
        # Check message count for rotation
        current_count = self.session_message_counts.get(current_session_id, 0)
        
        prompt_message = text
        is_new_session_from_rotation = False
        
        if current_count >= 25:
            logger.info(f"[telegram] Session {current_session_id} reached 25 messages. Rotating.")
            # Rotation logic
            old_session_id = current_session_id
            
            # Create NEW session
            current_session_id = self._create_new_session_id(user_id)
            self.user_sessions[user_id] = current_session_id
            self.session_message_counts[current_session_id] = 0
            is_new_session_from_rotation = True
            
            # Generate summary context
            context_summary = await self._generate_rotation_context(old_session_id)
            
            # Construct prompt with context
            prompt_message = (
                f"{context_summary}\n\n"
                f"[User Request] {text}"
            )
            
            # Send notification to user about rotation
            await self._send_message(chat_id, "🔄 Starting new session with summary of previous conversation...")

        # Increment count
        self.session_message_counts[current_session_id] += 1
        
        # 2. Indicate User Activity (On Demand)
        await heartbeat_state.start_on_demand()
        
        # 3. Process with LLM
        # We need a client instance.
        
        client = client_state.get_client(cwd=settings.AGENT_HOME_PATH)
        
        try:
            # Start typing indicator
            typing_task = asyncio.create_task(self._typing_loop(chat_id))

            # Prepare prompt
            final_prompt = prompt_message
            if self.session_message_counts[current_session_id] == 1:
                # Prepend instruction to the top of prompt (for both new and rotated sessions)
                # If rotated, prompt_message is "[Summary] ... [User Request] ...".
                # If new, prompt_message is just text.
                final_prompt = f"(Read CORE.md file first unless this request is simple and requires no context at all ->) {prompt_message}"
            
            # Execute Codex
            # We want to stream the output to capture the full response
            # But specific to Telegram, we just collect it and send it at the end.
            # Telegram doesn't support streaming well for bots in this way easily without editing messages constantly.
            # For 1.0, wait for full response.
            
            logger.info(f"[telegram] Sending message to Codex session {current_session_id}")
            
            user_timestamp = datetime.now()
            
            # Save user message first
            history_service.save_message(
                session_id=current_session_id,
                role="user",
                content=text, # Save original text, not the prompt with instruction/summary
                timestamp=user_timestamp
            )
            
            cli_output = client.exec_prompt(
                final_prompt,
                session_id=current_session_id,
                skip_git_repo_check=True,
                allow_edit=True
            )
            
            serialized = client.serialize_output(cli_output)
            
            agent_content = []
            serialized_output = []
            metadata = None
            
            for tag, line in serialized:
                serialized_output.append({"tag": tag, "data": line})
                client_state.check_and_update_state([{"tag": tag, "data": line}])
                
                if tag == "agent":
                    agent_content.append(line)
                elif tag == "meta":
                    try:
                        metadata = json.loads(line)
                    except:
                        pass
            
            full_response = "".join(agent_content)
            
            # Save assistant message
            history_service.save_message(
                session_id=current_session_id,
                role="assistant",
                content=full_response or "Complete",
                serialized_output=serialized_output,
                metadata=metadata
            )
            
            # Send response to Telegram
            if full_response:
                # Split if too long (Telegram limit is 4096)
                await self._send_long_message(chat_id, full_response)
            else:
                await self._send_message(chat_id, "✅ Task completed (no output).")
                
        except Exception as e:
            logger.error(f"[telegram] Error processing message: {e}")
            await self._send_message(chat_id, f"⚠️ Error: {str(e)}")
        finally:
            # Create a task to ensure typing loop is cancelled properly
            if 'typing_task' in locals():
                typing_task.cancel()
                try:
                    await typing_task
                except asyncio.CancelledError:
                    pass

            await heartbeat_state.end_on_demand()
    
    def _create_new_session_id(self, user_id):
        """Create a new session ID with telegram prefix."""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"telegram-{user_id}-{timestamp}"

    async def _send_message(self, chat_id, text):
        """Send message to Telegram."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._send_message_sync(chat_id, text))

    def _send_message_sync(self, chat_id, text):
        try:
            json_data = {"chat_id": chat_id, "text": text}
            logger.info(f"[telegram] Sending message to {chat_id}: {text}")
            requests.post(
                f"{self.base_url}/sendMessage",
                json=json_data
            )
        except Exception as e:
            logger.error(f"[telegram] Failed to send message: {e}")

    async def _send_long_message(self, chat_id, text):
        """Send long message by splitting."""
        # Simple splitting by 4000 chars
        chunk_size = 4000
        for i in range(0, len(text), chunk_size):
            await self._send_message(chat_id, text[i:i+chunk_size])

    async def _generate_rotation_context(self, old_session_id):
        """
        Generate summary of previous session.
        (1) Summary of first 15 messages.
        (2) Raw full bodies of last 10 messages.
        """
        history = history_service.get_conversation(old_session_id)
        if not history or not history.messages:
            return "No previous context."
        
        messages = history.messages
        total_msgs = len(messages)
        
        # We need ping-pongs (User+Assistant pairs usually, but history is flat list)
        # Let's just treat them as individual messages for slicing simplicity
        
        # Logic asked: "first 15 messages (both messages sent ping-pong...)"
        # and "last 10 message ping-pongs". 
        # "15 messages" probably means 15 turns or 15 individual messages.
        # "last 10 message ping-pongs" means 20 messages.
        
        # Let's interpret as:
        # First 15 individual messages -> Summarize.
        # Last 10 exchanges (20 messages) -> Keep raw.
        # Any overlap? If total is small, just keep raw.
        
        if total_msgs < 20: 
            # Just keep everything raw if it's short, though we rotated at 25 user messages (so ~50 total)
            pass
            
        first_chunk = messages[:15]
        last_chunk = messages[-20:] # Last 10 ping-pongs approx 20 msgs
        
        summary_text = await self._summarize_messages(first_chunk)
        
        raw_text = "\n[Latest Conversation]\n"
        for msg in last_chunk:
            role = "Agent" if msg.role == "assistant" else "User"
            raw_text += f"{role}: {msg.content}\n"
            
        return f"{summary_text}\n\n{raw_text}"

    async def _summarize_messages(self, messages):
        """Use Codex to summarize messages."""
        if not messages:
            return ""
            
        text_to_summarize = ""
        for msg in messages:
             role = "Agent" if msg.role == "assistant" else "User"
             text_to_summarize += f"{role}: {msg.content}\n"
             
        prompt = f"Summarize the following conversation context briefly:\n\n{text_to_summarize}"
        
        # Create a temp client to run this summary
        client = client_state.get_client(cwd=settings.AGENT_HOME_PATH)
        
        try:
            # We use a temporary session or no session? 
            # No session ID = stateless prompt (mostly).
            # But exec_prompt requires session_id usually for history tracking if we want it.
            # Here we just want a one-off.
             
            cli_output = client.exec_prompt(
                prompt,
                session_id=None, # One-off
                skip_git_repo_check=True
            )
            
            output_text = ""
            for tag, line in client.serialize_output(cli_output):
                if tag == "agent":
                    output_text += line
            
            return f"[Summary of Conversation Before]\n{output_text}"
        except Exception as e:
            logger.error(f"[telegram] Failed to summarize: {e}")
            return "[Failed to generate summary]"

    async def _typing_loop(self, chat_id):
        """Continuously send typing action."""
        try:
            while True:
                await self._send_chat_action(chat_id, "typing")
                # Telegram typing status lasts for ~5 seconds. Renew every 4s.
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"[telegram] Typing loop error: {e}")

    async def _send_chat_action(self, chat_id, action="typing"):
        """Send a chat action (like typing) to Telegram."""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._send_chat_action_sync(chat_id, action))

    def _send_chat_action_sync(self, chat_id, action):
        try:
            data = {"chat_id": chat_id, "action": action}
            requests.post(
                f"{self.base_url}/sendChatAction",
                json=data,
                timeout=5
            )
        except Exception as e:
            logger.error(f"[telegram] Failed to send chat action: {e}")



telegram_service = TelegramService()
