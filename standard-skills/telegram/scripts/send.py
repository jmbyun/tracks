#!/usr/bin/env python3
"""
Send messages to users via Telegram

Usage:
    send.py <message>

Examples:
    send.py "Hello, world!"
"""
import sys
import os
import json
import urllib.request
import urllib.error

def main():
    if len(sys.argv) < 2:
        print("Usage: python send.py 'message_content'", file=sys.stderr)
        sys.exit(1)
        
    message = sys.argv[1]
    
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    user_ids_str = os.environ.get("TELEGRAM_USER_IDS")
    
    if not bot_token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    if not user_ids_str:
        print("Error: TELEGRAM_USER_IDS environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    user_ids = [uid.strip() for uid in user_ids_str.split(",") if uid.strip()]
    
    base_url = f"https://api.telegram.org/bot{bot_token}"
    
    success = True
    for user_id in user_ids:
        try:
            url = f"{base_url}/sendMessage"
            data = json.dumps({
                "chat_id": user_id,
                "text": message
            }).encode('utf-8')
            
            req = urllib.request.Request(
                url, 
                data=data, 
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
            print(f"Message sent to {user_id}")
            
        except urllib.error.HTTPError as e:
            print(f"Failed to send message to {user_id}: HTTP Error {e.code}", file=sys.stderr)
            print(f"Response: {e.read().decode('utf-8')}", file=sys.stderr)
            success = False
        except urllib.error.URLError as e:
            print(f"Failed to send message to {user_id}: {e.reason}", file=sys.stderr)
            success = False
        except Exception as e:
            print(f"Failed to send message to {user_id}: {e}", file=sys.stderr)
            success = False
            
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
