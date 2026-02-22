#!/usr/bin/env python3
import sys
import argparse
from auth import make_instagram_request

def list_media(limit=10):
    try:
        # Fetch user's media
        results = make_instagram_request(f"me/media?fields=id,caption,media_type,media_url,permalink,timestamp,thumbnail_url&limit={limit}")
        media_list = results.get('data', [])
        
        if not media_list:
            print("No media posts found on this account.")
            return

        print(f"Found {len(media_list)} recent posts:")
        print("=" * 70)
        
        for media in media_list:
            print(f"Post ID:    {media.get('id')}")
            print(f"Type:       {media.get('media_type')}")
            print(f"Date:       {media.get('timestamp')}")
            print(f"Caption:    {media.get('caption', 'No Caption')}")
            if media.get('media_type') == 'VIDEO':
                print(f"Thumbnail:  {media.get('thumbnail_url', 'N/A')}")
            else:
                print(f"Media URL:  {media.get('media_url', 'N/A')}")
            print(f"Permalink:  {media.get('permalink')}")
            print("-" * 70)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List recent media posts from Instagram.')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of posts to return')
    args = parser.parse_args()
    
    list_media(limit=args.limit)
