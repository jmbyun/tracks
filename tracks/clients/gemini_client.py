from typing import Optional, Generator, Tuple, Dict, Any, List

import subprocess
import os
import json
import uuid
from pathlib import Path

from tracks.config import settings
from tracks.vault import vault

OUTPUT_TAG_STDOUT = 0
OUTPUT_TAG_STDERR = 1


class GeminiClient:
    """Python wrapper for Gemini CLI - Compatible with CodexClient interface"""
    
    def __init__(self, binary_path: Optional[str] = None, cwd: Optional[str] = None):
        """
        Initialize Gemini client
        
        Args:
            binary_path: Path to gemini binary. If None, uses 'gemini' from PATH
            cwd: Working directory for Gemini CLI. If None, uses {real_cwd}/home
        """
        if binary_path is None:
            # Use 'gemini' from PATH environment variable
            self.binary_path = 'gemini'
        else:
            self.binary_path = binary_path
        
        # Set default cwd
        if cwd is None:
            self.cwd = os.path.join(os.getcwd(), 'home')
        else:
            self.cwd = cwd
        
        # Setup config file (for compatibility, may be customized later)
        self._setup_config()
    
    def _setup_config(self):
        """
        Setup Gemini CLI config files by reading base templates from assets/,
        replacing {root} placeholders, and saving to {cwd}/.gemini/
        
        Files copied:
        - assets/settings.base.json -> {cwd}/.gemini/settings.json
        """
        # Get the directory containing this file (tracks/)
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        
        # Get the project root directory (parent of tracks/)
        root_path = os.path.dirname(current_file_path)
        
        # Ensure .gemini directory exists in cwd
        gemini_dir = os.path.join(self.cwd, '.gemini')
        os.makedirs(gemini_dir, exist_ok=True)
        
        # Copy settings.base.json -> settings.json
        settings_base_path = os.path.join(current_file_path, '..', 'assets', 'settings.base.json')
        settings_base_path = os.path.normpath(settings_base_path)
        
        try:
            with open(settings_base_path, 'r') as f:
                settings_content = f.read()
            
            # Replace all {root} placeholders with absolute root path
            settings_content = settings_content.replace('{root}', root_path)
            
            # Write to settings.json
            settings_path = os.path.join(gemini_dir, 'settings.json')
            with open(settings_path, 'w') as f:
                f.write(settings_content)
            
            print(f'[gemini] Settings written to: {settings_path}')
            
        except FileNotFoundError:
            # Settings template not found, skip
            print(f'[gemini] No settings template found at {settings_base_path}')
        except Exception as e:
            print(f'[gemini] Warning: Failed to setup settings: {e}')
    
    def _get_sessions_dir(self) -> Path:
        """Get the sessions directory path"""
        return Path(settings.STORAGE_PATH) / 'gemini_sessions'
    
    def _get_session_path(self, session_id: str) -> Path:
        """Get the session file path for a given session ID"""
        return self._get_sessions_dir() / f'{session_id}.jsonl'
    
    def create_session(self) -> str:
        """
        Create a new session and return its ID
        
        Returns:
            str: New session ID (UUID)
        """
        session_id = str(uuid.uuid4())
        sessions_dir = self._get_sessions_dir()
        sessions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create empty session file
        session_path = self._get_session_path(session_id)
        session_path.touch()
        
        print(f'[gemini] Created new session: {session_id}')
        return session_id
    
    def _append_to_session(self, session_id: str, event: Dict[str, Any]):
        """Append an event to the session file"""
        session_path = self._get_session_path(session_id)
        if not session_path.exists():
            session_path.touch()
        with open(session_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
    
    def _read_session_history(self, session_id: str) -> str:
        """Read the session history as a string"""
        session_path = self._get_session_path(session_id)
        if session_path.exists():
            return session_path.read_text()
        return ''
    
    def exec_prompt(
        self,
        prompt: str,
        session_id: Optional[str] = None,
        skip_git_repo_check: bool = False,
        allow_edit: bool = False,
        cwd: Optional[str] = None,
        model: Optional[str] = None
    ) -> Generator[Tuple[int, str], None, None]:
        """
        Execute a prompt using gemini CLI with PTY for unbuffered streaming
        
        Args:
            prompt: The prompt to execute
            session_id: Session ID for resuming. If provided, history is loaded from
                       cache/gemini/sessions/{session_id}.jsonl
            skip_git_repo_check: Skip git repo check (not used in Gemini)
            allow_edit: Allow dangerous edits (uses --yolo flag)
            cwd: Working directory
            model: Model to use (e.g., 'gemini-2.5-pro', 'gemini-2.5-flash')
            
        Yields:
            Tuple[int, str]: (tag, line) tuples where tag is OUTPUT_TAG_STDOUT or OUTPUT_TAG_STDERR
        """
        import pty
        import select
        
        # Use instance cwd as default if not provided
        if cwd is None:
            cwd = self.cwd
        
        # Create new session if not provided
        if session_id is None:
            session_id = self.create_session()
        
        # Store current session_id in instance for serialize_output to access
        self.current_session_id = session_id
        
        # Append user message to session
        user_message_event = {
            'type': 'message',
            'role': 'user',
            'content': prompt,
            'timestamp': self._get_timestamp()
        }
        self._append_to_session(session_id, user_message_event)
        
        # Read session history for stdin
        session_history = self._read_session_history(session_id)
        
        # Yield synthetic init event with our session_id
        init_event = json.dumps({'type': 'init', 'session_id': session_id})
        yield (OUTPUT_TAG_STDOUT, init_event + '\n')
        
        # Build command - use stdin for history
        cmd = [self.binary_path, '--prompt', prompt, '--output-format', 'stream-json']
        
        # Gemini doesn't have skip_git_repo_check equivalent
        # skip_git_repo_check is ignored
        
        if allow_edit:
            cmd.append('--yolo')
        
        if model:
            cmd.extend(['--model', model])
        
        print(f'[gemini] Spawning: {" ".join(cmd)}')
        print(f'[gemini] Session ID: {session_id}')
        print(f'[gemini] Binary path: {self.binary_path}')
        
        # Prepare environment with unbuffered output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['TERM'] = 'dumb'  # Simple terminal to avoid escape sequences
        # env['GEMINI_CONFIG_DIR'] = os.path.join(settings.STORAGE_PATH, "agent_configs", "gemini")
        env['AGENT_HOME_PATH'] = settings.AGENT_HOME_PATH

        # Add vault variables to environment
        for key, value in vault.to_dict().items():
            env[key] = value

        # Create PTY for stdout (forces line buffering in child process)
        master_fd, slave_fd = pty.openpty()
        
        # Start process with PTY as stdout, pipe stdin for history
        proc = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            cwd=cwd,
            env=env,
            bufsize=0
        )
        
        # Close slave in parent
        os.close(slave_fd)
        
        # Write session history to stdin and close
        if session_history:
            try:
                proc.stdin.write(session_history.encode('utf-8'))
            except:
                pass
        try:
            proc.stdin.close()
        except:
            pass
        
        try:
            import fcntl
            
            # Set master_fd and stderr to non-blocking
            flags_master = fcntl.fcntl(master_fd, fcntl.F_GETFL)
            fcntl.fcntl(master_fd, fcntl.F_SETFL, flags_master | os.O_NONBLOCK)
            
            flags_err = fcntl.fcntl(proc.stderr, fcntl.F_GETFL)
            fcntl.fcntl(proc.stderr, fcntl.F_SETFL, flags_err | os.O_NONBLOCK)
            
            stdout_buffer = b''
            stderr_buffer = b''
            
            # Accumulate full logs for debug printing on failure
            full_stdout = b''
            full_stderr = b''
            
            while True:
                # Check if process has finished
                if proc.poll() is not None:
                    # Read any remaining data
                    try:
                        while True:
                            remaining_out = os.read(master_fd, 4096)
                            if not remaining_out:
                                break
                            stdout_buffer += remaining_out
                            full_stdout += remaining_out
                    except (OSError, IOError):
                        pass
                    try:
                        remaining_err = proc.stderr.read()
                        if remaining_err:
                            stderr_buffer += remaining_err
                            full_stderr += remaining_err
                    except:
                        pass
                    break
                
                # Wait for data to be available
                try:
                    readable, _, _ = select.select([master_fd, proc.stderr], [], [], 0.05)
                except (ValueError, OSError):
                    break
                
                for stream in readable:
                    try:
                        if stream == master_fd:
                            data = os.read(master_fd, 4096)
                        else:
                            data = stream.read(4096)
                        
                        if not data:
                            continue
                            
                        if stream == master_fd:
                            stdout_buffer += data
                            full_stdout += data
                        else:
                            stderr_buffer += data
                            full_stderr += data
                    except (OSError, IOError):
                        pass
                
                # Process complete lines from stdout
                while b'\n' in stdout_buffer:
                    line, stdout_buffer = stdout_buffer.split(b'\n', 1)
                    decoded_line = line.decode('utf-8', errors='replace') + '\n'
                    
                    # Append to session file if it's valid JSON
                    try:
                        event = json.loads(decoded_line.strip())
                        self._append_to_session(session_id, event)
                    except json.JSONDecodeError:
                        pass
                    
                    yield (OUTPUT_TAG_STDOUT, decoded_line)
                
                # Process complete lines from stderr
                while b'\n' in stderr_buffer:
                    line, stderr_buffer = stderr_buffer.split(b'\n', 1)
                    yield (OUTPUT_TAG_STDERR, line.decode('utf-8', errors='replace') + '\n')
            
            # Yield any remaining buffered data
            if stdout_buffer:
                for line in stdout_buffer.decode('utf-8', errors='replace').splitlines(keepends=True):
                    if line:
                        # Append to session file if it's valid JSON
                        try:
                            event = json.loads(line.strip())
                            self._append_to_session(session_id, event)
                        except json.JSONDecodeError:
                            pass
                        yield (OUTPUT_TAG_STDOUT, line)
            
            if stderr_buffer:
                for line in stderr_buffer.decode('utf-8', errors='replace').splitlines(keepends=True):
                    if line:
                        yield (OUTPUT_TAG_STDERR, line)
            
            # Check for non-zero return code and print debug info
            return_code = proc.poll()
            if return_code is not None and return_code != 0:
                print("\n" + "="*50)
                print(f"Gemini exec ended with error (exit code: {return_code})")
                print("="*50)
                print("FULL STDOUT:")
                print(full_stdout.decode('utf-8', errors='replace'))
                print("-" * 30)
                print("FULL STDERR:")
                print(full_stderr.decode('utf-8', errors='replace'))
                print("="*50 + "\n")
            
        finally:
            # Ensure process is cleaned up
            os.close(master_fd)
            if proc.poll() is None:
                proc.kill()
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
    
    def serialize_output(
        self,
        output: Generator[Tuple[int, str], None, None]
    ) -> Generator[Tuple[str, str], None, None]:
        """
        Serialize raw output into structured events
        
        Gemini CLI with --output-format stream-json outputs JSONL with event types:
        - init: Session starts (includes session_id, model)
        - message: User prompts and assistant responses
        - tool_use: Tool call requests with parameters
        - tool_result: Tool execution results (success/error)
        - error: Non-fatal errors and warnings
        - result: Final session outcome with aggregated stats
        
        Args:
            output: Raw output from exec_prompt
            
        Yields:
            Tuple[str, str]: (event_type, data) tuples compatible with CodexClient
        """
        meta_dict = {}
        meta_emitted = False
        
        for tag, line in output:
            trimmed_line = line.strip()
            
            # Skip empty lines
            if not trimmed_line:
                continue
            
            # Handle stderr (non-JSON output)
            if tag == OUTPUT_TAG_STDERR:
                yield ('stderr', line)
                continue
            
            # Handle stdout - should be JSONL from stream-json format
            try:
                event = json.loads(trimmed_line)
                event_type = event.get('type', 'unknown')
                
                if event_type == 'init':
                    # Only emit meta once (from our synthetic init event)
                    # Gemini CLI also emits init event, but we keep our session_id
                    if not meta_emitted:
                        meta_dict['session_id'] = event.get('session_id', '')
                        meta_dict['model'] = event.get('model', '')
                        yield ('meta', json.dumps(meta_dict))
                        meta_emitted = True
                    else:
                        # From Gemini CLI's init, only update model info if present
                        gemini_model = event.get('model', '')
                        if gemini_model:
                            meta_dict['model'] = gemini_model
                
                elif event_type == 'message':
                    role = event.get('role', '')
                    content = event.get('content', '')
                    
                    if role == 'user':
                        yield ('title', 'User')
                        yield ('user', content + '\n')
                    elif role == 'assistant':
                        # Check if this is a delta (streaming) or complete message
                        is_delta = event.get('delta', False)
                        if is_delta:
                            yield ('stdout', content)
                        else:
                            yield ('title', 'Stdout')
                            yield ('stdout', content + '\n')
                
                elif event_type == 'tool_use':
                    tool_name = event.get('tool_name', 'unknown')
                    tool_id = event.get('tool_id', '')
                    parameters = event.get('parameters', {})
                    
                    yield ('title', 'Run')
                    yield ('exec', f'{tool_name}: {json.dumps(parameters)}\n')
                
                elif event_type == 'tool_result':
                    tool_id = event.get('tool_id', '')
                    status = event.get('status', '')
                    output_text = event.get('output', '')
                    
                    if status == 'success':
                        yield ('exec_output', output_text + '\n')
                    else:
                        yield ('exec_error', output_text + '\n')
                
                elif event_type == 'error':
                    error_msg = event.get('message', str(event))
                    yield ('error', error_msg + '\n')
                
                elif event_type == 'result':
                    # Final result with stats
                    stats = event.get('stats', {})
                    
                    # Extract token usage if available
                    total_tokens = stats.get('total_tokens', 0)
                    if total_tokens:
                        yield ('tokens_used', str(total_tokens))
                    
                    # Status is not yielded to avoid printing "success" in output
                
                else:
                    # Unknown event type, pass through as raw
                    yield ('raw', json.dumps(event) + '\n')
                    
            except json.JSONDecodeError:
                # Non-JSON output from stdout, treat as raw output
                yield ('stdout', line)
        
        yield ('done', '')
