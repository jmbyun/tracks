#!/usr/bin/env python3
import sys
import argparse
from auth import make_instagram_request

def list_comments(media_id):
    try:
        results = make_instagram_request(f"{media_id}/comments?fields=id,text,username,timestamp,replies")
        comments = results.get('data', [])
        
        if not comments:
            print(f"No comments found for post {media_id}.")
            return

        print(f"Found {len(comments)} comments on post {media_id}:")
        print("=" * 60)
        
        for c in comments:
            print(f"Comment ID: {c.get('id')}")
            print(f"Author:     {c.get('username')}")
            print(f"Date:       {c.get('timestamp')}")
            print(f"Text:       {c.get('text')}")
            
            replies = c.get('replies', {}).get('data', [])
            if replies:
                print("  Replies:")
                for r in replies:
                    print(f"    - {r.get('username')}: {r.get('text')} (ID: {r.get('id')})")
            print("-" * 60)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

def reply_to_comment(comment_id, message):
    try:
        # Note: Replying requires `instagram_manage_comments` scope on the token
        data = {"message": message}
        result = make_instagram_request(f"{comment_id}/replies", method="POST", data=data)
        
        reply_id = result.get('id')
        print(f"Successfully replied to comment {comment_id}!")
        print(f"New Reply ID: {reply_id}")
        
    except Exception as e:
        print(f"An error occurred while replying: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Manage comments on Instagram posts.')
    subparsers = parser.add_subparsers(dest='action', required=True)
    
    # List parser
    list_parser = subparsers.add_parser('list', help='List comments on a specific post')
    list_parser.add_argument('media_id', type=str, help='The ID of the Instagram Media/Post')
    
    # Reply parser
    reply_parser = subparsers.add_parser('reply', help='Reply to a specific comment')
    reply_parser.add_argument('comment_id', type=str, help='The ID of the comment to reply to')
    reply_parser.add_argument('message', type=str, help='The text content of the reply')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        list_comments(args.media_id)
    elif args.action == 'reply':
        reply_to_comment(args.comment_id, args.message)
