#!/usr/bin/env python3
import sys
import argparse
from auth import make_instagram_request

def search_my_media(query, limit=50):
    try:
        # Fetch user's media
        results = make_instagram_request(f"me/media?fields=id,caption,media_type,media_url,permalink,timestamp&limit={limit}")
        media_list = results.get('data', [])
        
        if not media_list:
            print("No media posts found on this account.")
            return

        query_lower = query.lower()
        matched_media = []
        for media in media_list:
            caption = media.get('caption', '')
            if caption and query_lower in caption.lower():
                matched_media.append(media)

        if not matched_media:
            print(f"No posts found matching '{query}'.")
            return

        print(f"Found {len(matched_media)} posts matching '{query}':")
        print("=" * 70)
        
        for media in matched_media:
            print(f"Post ID:    {media.get('id')}")
            print(f"Type:       {media.get('media_type')}")
            print(f"Date:       {media.get('timestamp')}")
            print(f"Caption:    {media.get('caption')}")
            if media.get('media_type') != 'VIDEO':
                print(f"Media URL:  {media.get('media_url', 'N/A')}")
            print(f"Permalink:  {media.get('permalink')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search your own Instagram media posts by caption.')
    parser.add_argument('query', type=str, help='The text to search for in your captions')
    parser.add_argument('--limit', type=int, default=50, help='Total number of recent posts to scan')
    args = parser.parse_args()
    
    if args.limit < 1:
        args.limit = 50
        
    search_my_media(args.query, limit=args.limit)
