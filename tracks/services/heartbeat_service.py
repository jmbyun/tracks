"""
Heartbeat background task service for managing LLM work when user is inactive.
"""

import asyncio
import os
from datetime import datetime
from typing import Optional, Callable, Awaitable

from ..config import settings


# Heartbeat prompt to send to LLM
HEARTBEAT_PROMPT = (
    "[HEARTBEAT] Work on the tasks in `JOURNAL.md`."
)


class HeartbeatState:
    """
    Singleton class to manage heartbeat and on_demand state flags.
    
    Flags:
        heartbeat: True when Background Task LLM is responding or within cooldown
        on_demand: True when user request is being processed or within cooldown
    """
    
    _instance: Optional['HeartbeatState'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # Flag states
        self._heartbeat: bool = False
        self._on_demand: bool = False
        
        # Timers for cooldown
        self._heartbeat_timer: Optional[asyncio.TimerHandle] = None
        self._on_demand_timer: Optional[asyncio.TimerHandle] = None
        
        # Heartbeat session management
        self._heartbeat_session_id: Optional[str] = None
        self._heartbeat_session_date: Optional[str] = None
        
        # Callback for triggering heartbeat task
        self._trigger_callback: Optional[Callable[[], Awaitable[None]]] = None
        
        # Lock for thread safety
        self._lock = asyncio.Lock()
    
    def set_trigger_callback(self, callback: Callable[[], Awaitable[None]]):
        """Set the callback function to trigger heartbeat task."""
        self._trigger_callback = callback
    
    @property
    def heartbeat(self) -> bool:
        return self._heartbeat
    
    @property
    def on_demand(self) -> bool:
        return self._on_demand
    
    @property
    def heartbeat_session_id(self) -> Optional[str]:
        return self._heartbeat_session_id
    
    def set_heartbeat_session_id(self, session_id: str):
        """Set heartbeat session ID and update date."""
        self._heartbeat_session_id = session_id
        self._heartbeat_session_date = datetime.now().strftime("%Y-%m-%d")
    
    def should_create_new_session(self) -> bool:
        """Check if a new heartbeat session should be created (always True now)."""
        return True
    
    async def start_heartbeat(self):
        """Mark heartbeat task as active."""
        async with self._lock:
            # Cancel any pending cooldown timer
            if self._heartbeat_timer:
                self._heartbeat_timer.cancel()
                self._heartbeat_timer = None
            
            self._heartbeat = True
            print(f"[heartbeat] heartbeat flag set to True")
    
    async def end_heartbeat(self):
        """
        Mark heartbeat task as complete. 
        Will transition to False after cooldown period.
        """
        async with self._lock:
            # Cancel any existing timer
            if self._heartbeat_timer:
                self._heartbeat_timer.cancel()
            
            # Schedule transition to False after cooldown
            loop = asyncio.get_event_loop()
            self._heartbeat_timer = loop.call_later(
                settings.HEARTBEAT_COOLDOWN_SECONDS,
                lambda: asyncio.create_task(self._heartbeat_cooldown_expired())
            )
            print(f"[heartbeat] heartbeat cooldown started ({settings.HEARTBEAT_COOLDOWN_SECONDS}s)")
    
    async def _heartbeat_cooldown_expired(self):
        """Called when heartbeat cooldown expires."""
        async with self._lock:
            was_true = self._heartbeat
            self._heartbeat = False
            self._heartbeat_timer = None
            print(f"[heartbeat] heartbeat flag set to False")
            
            # Reactive effect: trigger heartbeat if on_demand is also False
            if was_true and not self._on_demand:
                print(f"[heartbeat] Both flags False after heartbeat cooldown, triggering heartbeat task")
                if self._trigger_callback:
                    asyncio.create_task(self._trigger_callback())
    
    async def start_on_demand(self):
        """Mark on-demand (user) request as active."""
        async with self._lock:
            # Cancel any pending cooldown timer
            if self._on_demand_timer:
                self._on_demand_timer.cancel()
                self._on_demand_timer = None
            
            self._on_demand = True
            print(f"[heartbeat] on_demand flag set to True")
    
    async def end_on_demand(self):
        """
        Mark on-demand request as complete.
        Will transition to False after cooldown period.
        """
        async with self._lock:
            # Cancel any existing timer
            if self._on_demand_timer:
                self._on_demand_timer.cancel()
            
            # Schedule transition to False after cooldown
            loop = asyncio.get_event_loop()
            self._on_demand_timer = loop.call_later(
                settings.ON_DEMAND_COOLDOWN_SECONDS,
                lambda: asyncio.create_task(self._on_demand_cooldown_expired())
            )
            print(f"[heartbeat] on_demand cooldown started ({settings.ON_DEMAND_COOLDOWN_SECONDS}s)")
    
    async def _on_demand_cooldown_expired(self):
        """Called when on_demand cooldown expires."""
        async with self._lock:
            was_true = self._on_demand
            self._on_demand = False
            self._on_demand_timer = None
            print(f"[heartbeat] on_demand flag set to False")
            
            # Reactive effect: trigger heartbeat if heartbeat is also False
            if was_true and not self._heartbeat:
                print(f"[heartbeat] Both flags False after on_demand cooldown, triggering heartbeat task")
                if self._trigger_callback:
                    asyncio.create_task(self._trigger_callback())
    
    def get_status(self) -> dict:
        """Get current status of the heartbeat system."""
        return {
            "heartbeat": self._heartbeat,
            "on_demand": self._on_demand,
            "heartbeat_session_id": self._heartbeat_session_id,
            "heartbeat_session_date": self._heartbeat_session_date,
            "heartbeat_cooldown_seconds": settings.HEARTBEAT_COOLDOWN_SECONDS,
            "on_demand_cooldown_seconds": settings.ON_DEMAND_COOLDOWN_SECONDS,
        }


# Singleton instance
heartbeat_state = HeartbeatState()
