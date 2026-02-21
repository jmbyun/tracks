import sys
import json
import os

def from_root(path: str):
    return os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), path))

def update_api_key(new_key):
    config_path = from_root("config.json")
    config = {}
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()
                if content.strip():
                    config = json.loads(content)
        except Exception as e:
            print(f"Error reading {config_path}: {e}")
    
    config["API_KEY"] = new_key
    
    try:
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
        print(f"Successfully updated API_KEY in {config_path}")
    except Exception as e:
        print(f"Error writing to {config_path}: {e}")

def print_usage():
    print("Usage: python setup.py apikey {api_key}")
    print("Example: python setup.py apikey my-secret-key-123")

if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "apikey":
        update_api_key(sys.argv[2])
    else:
        print_usage()
        sys.exit(1)
