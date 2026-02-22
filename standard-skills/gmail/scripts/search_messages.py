#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
from auth import make_gmail_request

def search_messages(query, max_results=10):
    try:
        # Build query parameters
        params = {
            'q': query,
            'maxResults': str(max_results)
        }
        params_str = urllib.parse.urlencode(params)
        
        # 1. Search messages
        results = make_gmail_request(f"messages?{params_str}")
        messages = results.get('messages', [])
        
        if not messages:
            print(f"No messages found matching query: '{query}'")
            return

        print(f"Found {len(messages)} messages matching '{query}':")
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
    parser = argparse.ArgumentParser(description='Search emails in Gmail using a query string.')
    parser.add_argument('query', type=str, help='The search query (e.g., "from:alice@example.com is:unread")')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of emails to return')
    args = parser.parse_args()
    
    search_messages(args.query, max_results=args.max_results)
