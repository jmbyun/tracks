#!/usr/bin/env python3
import sys
import argparse
import base64
from auth import make_gmail_request

def get_body(payload):
    """Deep search through message payload for text body."""
    if 'parts' in payload:
        for part in payload['parts']:
            if part.get('mimeType') == 'text/plain':
                data = part['body'].get('data')
                if data:
                    # Google API uses URL-safe base64
                    padded_data = data + '=' * (4 - len(data) % 4)
                    return base64.urlsafe_b64decode(padded_data).decode('utf-8')
            elif part.get('mimeType') == 'text/html':
                # Grab HTML if plain text isn't available
                html_data = part['body'].get('data')
                if html_data:
                    padded_data = html_data + '=' * (4 - len(html_data) % 4)
                    return base64.urlsafe_b64decode(padded_data).decode('utf-8')
            elif 'parts' in part:
                # Recurse
                nested_body = get_body(part)
                if nested_body:
                    return nested_body
    
    # Simple message without parts
    data = payload.get('body', {}).get('data')
    if data:
        padded_data = data + '=' * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(padded_data).decode('utf-8')

    return ""

def read_message(msg_id):
    try:
        msg = make_gmail_request(f"messages/{msg_id}?format=full")
        
        headers = msg.get('payload', {}).get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        to = next((h['value'] for h in headers if h['name'] == 'To'), 'Unknown Recipient')
        cc = next((h['value'] for h in headers if h['name'] == 'Cc'), None)
        
        body = get_body(msg.get('payload', {}))
        
        print(f"ID: {msg['id']}")
        print(f"Date: {date}")
        print(f"From: {sender}")
        print(f"To: {to}")
        if cc:
            print(f"Cc: {cc}")
        print(f"Subject: {subject}")
        print("=" * 60)
        print(body.strip() if body else "[No text content found in message]")
        print("=" * 60)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read a specific email from Gmail using its ID.')
    parser.add_argument('msg_id', type=str, help='The ID of the message to read (obtained from list or search)')
    args = parser.parse_args()
    
    read_message(args.msg_id)
