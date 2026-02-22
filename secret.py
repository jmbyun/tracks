import sys
import re
import json
import base64
import ast
from pathlib import Path

TARGET_PATH = str(Path(__file__).parent / "tracks/secret.py")

def hide_secrets():
    with open(TARGET_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    raw_match = re.search(r"^RAW_SECRET\s*=\s*(\{[\s\S]*?\})", content, re.MULTILINE)
    secret_match = re.search(r"^SECRET\s*=\s*None", content, re.MULTILINE)
    
    if not raw_match or not secret_match:
        print("Could not find 'RAW_SECRET = {...}' or 'SECRET = None' at the start of lines. Maybe already hidden?")
        return
        
    raw_secret_str = raw_match.group(1)
    
    try:
        raw_secret_dict = ast.literal_eval(raw_secret_str)
    except Exception as e:
        print(f"Failed to parse RAW_SECRET dict: {e}")
        return
        
    json_str = json.dumps(raw_secret_dict)
    b64_str = base64.b64encode(json_str.encode("utf-8")).decode("utf-8")
    
    content = re.sub(r"^RAW_SECRET\s*=\s*\{[\s\S]*?\}", "RAW_SECRET = None", content, count=1, flags=re.MULTILINE)
    content = re.sub(r"^SECRET\s*=\s*None", f'SECRET = "{b64_str}"', content, count=1, flags=re.MULTILINE)
    
    with open(TARGET_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Secrets hidden successfully!")


def show_secrets():
    with open(TARGET_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        
    raw_match = re.search(r"^RAW_SECRET\s*=\s*None", content, re.MULTILINE)
    secret_match = re.search(r'^SECRET\s*=\s*"([^"]*)"', content, re.MULTILINE)
    
    if not raw_match or not secret_match:
        print("Could not find 'RAW_SECRET = None' or 'SECRET = \"...\"' at the start of lines. Maybe already shown?")
        return
        
    b64_str = secret_match.group(1)
    
    try:
        json_str = base64.b64decode(b64_str).decode("utf-8")
        raw_secret_dict = json.loads(json_str)
    except Exception as e:
        print(f"Failed to decode SECRET: {e}")
        return
        
    lines = ["{"]
    for k, v in raw_secret_dict.items():
        lines.append(f'    "{k}": "{v}",')
    if len(lines) > 1:
        lines[-1] = lines[-1].rstrip(",")
    lines.append("}")
    dict_str = "\n".join(lines)
    
    content = re.sub(r"^RAW_SECRET\s*=\s*None", f"RAW_SECRET = {dict_str}", content, count=1, flags=re.MULTILINE)
    content = re.sub(r'^SECRET\s*=\s*"[^"]*"', "SECRET = None", content, count=1, flags=re.MULTILINE)
    
    with open(TARGET_PATH, "w", encoding="utf-8") as f:
        f.write(content)
        
    print("Secrets shown successfully!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python secret.py [hide|show]")
        sys.exit(1)
        
    cmd = sys.argv[1].lower()
    if cmd == "hide":
        hide_secrets()
    elif cmd == "show":
        show_secrets()
    else:
        print("Unknown command. Use 'hide' or 'show'.")
