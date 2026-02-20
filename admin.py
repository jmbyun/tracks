import argparse
import os
import subprocess
import sys

# Ensure the tracks module can be imported
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tracks.config import settings

def main():
    parser = argparse.ArgumentParser(description="Admin CLI for Tracks")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    agent_parser = subparsers.add_parser("agent", help="Run an agent")
    agent_parser.add_argument("agent_type", choices=["codex", "gemini"], help="The agent to run")
    agent_parser.add_argument("agent_args", nargs=argparse.REMAINDER, help="Arguments to pass to the agent")
    
    args = parser.parse_args()
    
    if args.command == "agent":
        agent_type = args.agent_type
        agent_home_path = settings.AGENT_HOME_PATH
        storage_path = settings.STORAGE_PATH
        
        env = os.environ.copy()
        
        if agent_type == "codex":
            config_dir = os.path.join(storage_path, "agent_configs", "codex")
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(agent_home_path, exist_ok=True)
            
            env["CODEX_HOME"] = config_dir
            cmd = ["codex"] + args.agent_args
            
            print(f"Running codex in {agent_home_path}")
            print(f"CODEX_HOME: {env['CODEX_HOME']}")
            
        elif agent_type == "gemini":
            config_dir = os.path.join(storage_path, "agent_configs", "gemini")
            os.makedirs(config_dir, exist_ok=True)
            os.makedirs(agent_home_path, exist_ok=True)
            
            env["GEMINI_CONFIG_DIR"] = config_dir
            cmd = ["gemini"] + args.agent_args
            
            print(f"Running gemini in {agent_home_path}")
            print(f"GEMINI_CONFIG_DIR: {env['GEMINI_CONFIG_DIR']}")
            
        try:
            subprocess.run(cmd, env=env, cwd=agent_home_path)
        except FileNotFoundError:
            print(f"Error: Could not find '{cmd[0]}' command. Make sure it is installed and in your PATH.")
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            pass
        except Exception as e:
            print(f"Error running {agent_type}: {e}")

if __name__ == "__main__":
    main()
