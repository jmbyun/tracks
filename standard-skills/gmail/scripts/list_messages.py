#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
from auth import make_gmail_request

def list_messages(max_results=10, label_ids=None):
    if label_ids is None:
        label_ids = ['INBOX']
        
    try:
        # Build query parameters
        params = {'maxResults': str(max_results)}
        for lid in label_ids:
            params['labelIds'] = lid
            
        params_str = urllib.parse.urlencode(params, doseq=True)
        
        # 1. Fetch message list
        results = make_gmail_request(f"messages?{params_str}")
        messages = results.get('messages', [])
        
        if not messages:
            print("No new messages found.")
            return

        print(f"Found {len(messages)} messages:")
        print("-" * 50)
        
        # 2. Fetch details for each message
        for message in messages:
            msg_id = message['id']
            msg = make_gmail_request(f"messages/{msg_id}?format=metadata&metadataHeaders=From&metadataHeaders=Subject&metadataHeaders=Date")
            
            headers = msg.get('payload', {}).get('headers', [])
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
            
            print(f"ID: {msg['id']}")
            print(f"Date: {date}")
            print(f"From: {sender}")
            print(f"Subject: {subject}")
            print(f"Snippet: {msg.get('snippet', '')}")
            print("-" * 50)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List recent emails from Gmail.')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of emails to return')
    parser.add_argument('--label', type=str, default='INBOX', help='Label ID to filter by (e.g. INBOX, SENT)')
    args = parser.parse_args()
    
    list_messages(max_results=args.max_results, label_ids=[args.label])
