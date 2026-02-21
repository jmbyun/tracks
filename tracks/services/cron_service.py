import os
import time
import asyncio
import subprocess
import shlex
from datetime import datetime, timezone, timedelta
from tracks.config import settings
import logging

def get_timezone():
    return timezone(timedelta(hours=settings.UTC_OFFSET))

logger = logging.getLogger(__name__)

class CronService:
    def __init__(self):
        self._task = None
        self._running = False
        self.crontab_file = os.path.join(settings.AGENT_HOME_PATH, "crontabs.txt")

    def start(self):
        if not self._running:
            self._running = True
            logger.info("[cron_service] Starting custom python cron scheduler")
            self._task = asyncio.create_task(self._run_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    async def _run_loop(self):
        while self._running:
            tz = get_timezone()
            now_dt = datetime.now(tz)
            # Wait until the start of the next minute
            # seconds_to_next_minute = 60 - now_dt.second
            seconds_to_next_minute = 60 - now_dt.second + 1
            await asyncio.sleep(seconds_to_next_minute)
            
            if not self._running:
                break
                
            current_time = datetime.now(tz)
            try:
                await self._check_and_run_jobs(current_time)
            except Exception as e:
                logger.error(f"[cron_service] Error running jobs: {e}")

    async def _check_and_run_jobs(self, current_time: datetime):
        logger.info(f"[cron_service] Checking for scheduled jobs at {current_time}")
        if not os.path.exists(self.crontab_file):
            logger.error(f"[cron_service] Crontab file not found: {self.crontab_file}")
            return

            
        try:
            with open(self.crontab_file, 'r') as f:
                lines = f.readlines()
        except Exception as e:
            logger.error(f"[cron_service] Failed to read crontab file: {e}")
            return
            
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split(maxsplit=5)
            if len(parts) < 6:
                continue
                
            minute_expr, hour_expr, day_expr, month_expr, dow_expr, command = parts
            
            if self._matches(minute_expr, current_time.minute) and \
               self._matches(hour_expr, current_time.hour) and \
               self._matches(day_expr, current_time.day) and \
               self._matches(month_expr, current_time.month) and \
               self._matches_dow(dow_expr, current_time):
                
                logger.info(f"[cron_service] Triggering scheduled job: {command}")
                # Execute command in background
                self._run_command(command)

    def _matches(self, expr: str, value: int) -> bool:
        if expr == '*':
            return True
        if expr.startswith('*/'):
            try:
                divisor = int(expr[2:])
                return value % divisor == 0
            except ValueError:
                return False
        
        # Exact match or list
        if ',' in expr:
            try:
                allowed = [int(v) for v in expr.split(',')]
                return value in allowed
            except ValueError:
                return False
                
        # Range
        if '-' in expr:
            try:
                start, end = [int(v) for v in expr.split('-')]
                return start <= value <= end
            except ValueError:
                return False
                
        try:
            return value == int(expr)
        except ValueError:
            return False

    def _matches_dow(self, expr: str, dt: datetime) -> bool:
        if expr == '*':
            return True
            
        # Python weekday: Monday is 0, Sunday is 6
        # Cron weekday: Sunday is 0 or 7
        curr_dow_cron = dt.weekday() + 1
        if curr_dow_cron == 7:
            curr_dow_cron = 0
            
        if expr.startswith('*/'):
            try:
                divisor = int(expr[2:])
                # Note: */X for DOW is unusual but supported
                return curr_dow_cron % divisor == 0 or (curr_dow_cron == 0 and 7 % divisor == 0)
            except ValueError:
                return False
                
        if ',' in expr:
            try:
                allowed = [int(v) for v in expr.split(',')]
                return curr_dow_cron in allowed or (curr_dow_cron == 0 and 7 in allowed)
            except ValueError:
                return False
                
        if '-' in expr:
            try:
                start, end = [int(v) for v in expr.split('-')]
                return start <= curr_dow_cron <= end or (curr_dow_cron == 0 and start <= 7 <= end)
            except ValueError:
                return False
                
        try:
            target = int(expr)
            return curr_dow_cron == target or (curr_dow_cron == 0 and target == 7)
        except ValueError:
            return False

    def _run_command(self, command: str):
        try:
            # We want to run this asynchronously from our main thread, Subprocess is good
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )
        except Exception as e:
            logger.error(f"[cron_service] Failed to execute job {command}: {e}")

cron_service = CronService()
