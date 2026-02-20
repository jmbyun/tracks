"""
FastAPI application initialization.
"""

import os
import shutil
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Security, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings
from .controllers import routers
from .services.heartbeat_service import heartbeat_state
from .services.heartbeat_runner import trigger_heartbeat_task
from .services.cron_service import cron_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager for startup/shutdown events."""
    # Startup: Initialize heartbeat system
    
    heartbeat_state.set_trigger_callback(trigger_heartbeat_task)
    
    print(f"[app] Heartbeat system initialized")

    # Copy standard-skills to agent home path upon startup
    standard_skills_dir = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../standard-skills"))
    target_skills_dir = os.path.join(settings.AGENT_HOME_PATH, "skills")
    
    if os.path.exists(standard_skills_dir):
        os.makedirs(target_skills_dir, exist_ok=True)
        for skill_name in os.listdir(standard_skills_dir):
            src_path = os.path.join(standard_skills_dir, skill_name)
            if os.path.isdir(src_path):
                dst_path = os.path.join(target_skills_dir, skill_name)
                try:
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    print(f"[app] Copied standard skill: {skill_name}")
                except Exception as e:
                    print(f"[app] Error copying standard skill {skill_name}: {e}")

    # Initialize core prompt files if missing
    core_src = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../prompts/CORE.md"))
    if os.path.exists(core_src):
        for target_name in ["GEMINI.md", "AGENTS.md"]:
            target_path = os.path.join(settings.AGENT_HOME_PATH, target_name)
            if not os.path.exists(target_path):
                try:
                    shutil.copy2(core_src, target_path)
                    print(f"[app] Initialized {target_name} from CORE.md")
                except Exception as e:
                    print(f"[app] Error initializing {target_name}: {e}")
    
    # Start background task to trigger initial heartbeat after ON_DEMAND_COOLDOWN_SECONDS
    initial_task = asyncio.create_task(_initial_heartbeat_trigger())
    print(f"[app] Initial heartbeat scheduled in {settings.ON_DEMAND_COOLDOWN_SECONDS}s")
    
    # Start Telegram polling
    from .services.telegram_service import telegram_service
    asyncio.create_task(telegram_service.start_polling())
    print(f"[app] Telegram polling service started")
    
    # Start Cron service
    cron_service.start()
    
    yield
    
    # Shutdown: cleanup
    telegram_service.is_running = False
    initial_task.cancel()
    cron_service.stop()
    print(f"[app] Shutting down heartbeat system, telegram service, and cron service")


async def _initial_heartbeat_trigger():
    """Trigger initial heartbeat if no user activity since startup."""
    # Wait for ON_DEMAND_COOLDOWN_SECONDS before triggering
    await asyncio.sleep(settings.ON_DEMAND_COOLDOWN_SECONDS)
    
    # Only trigger if both flags are still False (no user activity)
    if not heartbeat_state.heartbeat and not heartbeat_state.on_demand:
        print(f"[app] No user activity since startup, triggering initial heartbeat")
        await trigger_heartbeat_task()
    else:
        print(f"[app] User activity detected, skipping initial heartbeat")


security = HTTPBearer()


def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key from Authorization header."""
    if settings.API_KEY and credentials.credentials != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    return credentials.credentials


class App:
    """Main application class."""
    
    def __init__(self):
        """Initialize FastAPI application."""
        # Configure global dependencies if API_KEY is set
        dependencies = []
        if settings.API_KEY:
            dependencies.append(Security(verify_api_key))
            print(f"[app] API Key authentication enabled")
        
        self.web_app = FastAPI(
            title="Agents on Tracks API",
            description="Agents on Tracks API",
            version="0.1.0",
            lifespan=lifespan,
            dependencies=dependencies
        )
        
        self.setup_middleware()
        self.setup_routers()
    
    def setup_middleware(self):
        """Configure middleware."""
        self.web_app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def setup_routers(self):
        """Register all routers."""
        for router in routers:
            self.web_app.include_router(router)


# Create app instance
app_instance = App()
app = app_instance.web_app
