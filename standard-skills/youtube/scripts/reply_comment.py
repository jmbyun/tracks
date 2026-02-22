#!/usr/bin/env python3
import sys
import argparse
from auth import make_youtube_request

def reply_comment(parent_id, text):
    try:
        payload = {
            "snippet": {
                "parentId": parent_id,
                "textOriginal": text
            }
        }
            
        print(f"Posting reply to comment '{parent_id}'...")
        
        result = make_youtube_request("comments?part=snippet", method="POST", data=payload)
        
        reply_id = result.get('id')
        if reply_id:
            print(f"Successfully posted reply! (Reply ID: {reply_id})")
        else:
            print("Failed to get ID of the posted reply.")
            print(result)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Post a reply to an existing YouTube comment.')
    parser.add_argument('parent_id', type=str, help='The ID of the comment to reply to. (You can get this from read_comments.py)')
    parser.add_argument('text', type=str, help='The plain text content of the reply.')
    
    args = parser.parse_args()
    reply_comment(args.parent_id, args.text)
