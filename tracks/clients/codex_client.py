from typing import Optional, Generator, Tuple, Dict, Any

import subprocess
import os
import json
import re

from tracks.vault import vault
from tracks.config import settings

OUTPUT_TAG_STDOUT = 0
OUTPUT_TAG_STDERR = 1


class CodexClient:
    """Python wrapper for Codex CLI"""
    
    def __init__(self, binary_path: Optional[str] = None, cwd: Optional[str] = None, profile_id: str = "main"):
        """
        Initialize Codex client
        
        Args:
            binary_path: Path to codex binary. If None, uses 'codex' from PATH
            cwd: Working directory for Codex CLI. If None, uses AGENT_HOME_PATH
        """
        if binary_path is None:
            # Use 'codex' from PATH environment variable
            self.binary_path = 'codex'
        else:
            self.binary_path = binary_path
        
        # Set default cwd
        if cwd is None:
            self.cwd = settings.AGENT_HOME_PATH
        else:
            self.cwd = cwd

        self.profile_id = profile_id
        
        # Setup config file
        self._setup_config()
    
    def _setup_config(self):
        """
        Setup Codex CLI config file by reading config.base.toml template,
        replacing {root} placeholders, and saving to {cwd}/.codex/config.toml
        """
        # Get the directory containing this file
        current_file_path = os.path.dirname(os.path.abspath(__file__))
        
        # Get the root directory (same as current_file_path since codex_client.py is at root)
        root_path = current_file_path
        
        # Read config.base.toml template
        config_base_path = os.path.join(current_file_path, 'assets', 'config.base.toml')
        
        try:
            with open(config_base_path, 'r') as f:
                config_content = f.read()
            
            # Replace all {root} placeholders with absolute root path
            config_content = config_content.replace('{root}', root_path)
            
            # Ensure .codex directory exists in cwd
            codex_dir = os.path.join(self.cwd, '.codex')
            os.makedirs(codex_dir, exist_ok=True)
            
            # Write to config.toml
            config_path = os.path.join(codex_dir, 'config.toml')
            with open(config_path, 'w') as f:
                f.write(config_content)
            
            print(f'[cli] Config written to: {config_path}')
            
        except FileNotFoundError:
            print(f'[cli] Warning: config.base.toml not found at {config_base_path}')
        except Exception as e:
            print(f'[cli] Warning: Failed to setup config: {e}')
    
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
        Execute a prompt using codex CLI with PTY for unbuffered streaming
        
        Args:
            prompt: The prompt to execute
            session_id: Session ID for resuming
            skip_git_repo_check: Skip git repo check
            allow_edit: Allow dangerous edits
            cwd: Working directory
            model: Model to use
            
        Yields:
            Tuple[int, str]: (tag, line) tuples where tag is OUTPUT_TAG_STDOUT or OUTPUT_TAG_STDERR
        """
        import pty
        import select
        
        cmd = [self.binary_path, 'exec']
        
        # Use instance cwd as default if not provided
        if cwd is None:
            cwd = self.cwd
        
        if skip_git_repo_check:
            cmd.append('--skip-git-repo-check')
        
        if allow_edit:
            cmd.append('--dangerously-bypass-approvals-and-sandbox')
        
        if session_id:
            cmd.extend(['resume', session_id, prompt])
        else:
            cmd.append(prompt)
        
        print(f'[cli] Spawning: {" ".join(cmd)}')
        print(f'[cli] Binary path: {self.binary_path}')
        
        # Prepare environment with unbuffered output
        env = os.environ.copy()
        env['PYTHONUNBUFFERED'] = '1'
        env['TERM'] = 'dumb'  # Simple terminal to avoid escape sequences
        env['CODEX_HOME'] = os.path.join(settings.STORAGE_PATH, "codex_homes", self.profile_id)
        env['AGENT_HOME_PATH'] = settings.AGENT_HOME_PATH
        
        # Add vault variables to environment
        for key, value in vault.to_dict().items():
            env[key] = value

        # Create PTY for stdout (forces line buffering in child process)
        master_fd, slave_fd = pty.openpty()
        
        # Start process with PTY as stdout
        proc = subprocess.Popen(
            cmd,
            stdout=slave_fd,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,
            cwd=cwd,
            env=env,
            bufsize=0
        )
        
        # Close slave in parent
        os.close(slave_fd)
        
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
                    yield (OUTPUT_TAG_STDOUT, line.decode('utf-8', errors='replace') + '\n')
                
                # Process complete lines from stderr
                while b'\n' in stderr_buffer:
                    line, stderr_buffer = stderr_buffer.split(b'\n', 1)
                    yield (OUTPUT_TAG_STDERR, line.decode('utf-8', errors='replace') + '\n')
            
            # Yield any remaining buffered data
            if stdout_buffer:
                for line in stdout_buffer.decode('utf-8', errors='replace').splitlines(keepends=True):
                    if line:
                        yield (OUTPUT_TAG_STDOUT, line)
            
            if stderr_buffer:
                for line in stderr_buffer.decode('utf-8', errors='replace').splitlines(keepends=True):
                    if line:
                        yield (OUTPUT_TAG_STDERR, line)
            
            # Check for non-zero return code and print debug info
            return_code = proc.poll()
            if return_code is not None and return_code != 0:
                print("\n" + "="*50)
                print(f"Codex exec ended with error (exit code: {return_code})")
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
    
    def serialize_output(
        self,
        output: Generator[Tuple[int, str], None, None]
    ) -> Generator[Tuple[str, str], None, None]:
        """
        Serialize raw output into structured events
        
        Args:
            output: Raw output from exec_prompt
            
        Yields:
            Tuple[str, str]: (event_type, data) tuples
        """
        output_tag = None
        meta_done = False
        meta_dict = {}
        
        for tag, line in output:
            trimmed_line = line.strip()
            
            # Handle stdout tags
            if tag == OUTPUT_TAG_STDOUT:
                if output_tag != 'stdout':
                    output_tag = 'stdout'
                    yield ('title', 'Stdout')
                yield ('stdout', line)
                continue
            
            # Handle stderr tags
            if trimmed_line == 'user':
                output_tag = 'user'
                yield ('title', 'User')
                continue
            elif trimmed_line == 'thinking':
                output_tag = 'thinking'
                yield ('title', 'Thinking')
                continue
            elif trimmed_line == 'exec':
                output_tag = 'exec'
                yield ('title', 'Run')
                continue
            elif trimmed_line in ('kori', 'codex'):
                output_tag = 'agent'
                yield ('title', 'Agent')
                continue
            elif trimmed_line == 'file update:':
                output_tag = 'file_update'
                yield ('title', 'File Update')
                continue
            elif trimmed_line == 'tokens used':
                output_tag = 'tokens_used'
                continue
            
            # Handle metadata delimiters
            if not meta_done and re.match(r'^[-]{3,}$', trimmed_line):
                if output_tag != 'meta':
                    output_tag = 'meta'
                else:
                    output_tag = None
                    meta_done = True
                    yield ('meta', json.dumps(meta_dict))
                continue
            
            # Process content based on current tag
            if output_tag == 'meta':
                colon_index = line.find(':')
                if colon_index != -1:
                    key = line[:colon_index].strip().replace(' ', '_')
                    value = line[colon_index + 1:].strip()
                    meta_dict[key] = value
            elif output_tag == 'exec':
                # Match exec completion pattern
                exec_match = re.match(
                    r'^(.*) succeeded in ([0-9.,]+ms)(:)?(\s)*$',
                    line
                )
                if exec_match:
                    yield ('exec', exec_match.group(1) + '\n')
                    yield ('exec_time', exec_match.group(2))
                else:
                    yield ('exec_output', line)
            elif output_tag == 'tokens_used':
                yield ('tokens_used', trimmed_line.replace(',', ''))
            elif output_tag is not None:
                yield (output_tag, line)
        
        yield ('done', '')
