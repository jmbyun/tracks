#!/usr/bin/env python3
import sys
import argparse
from auth import make_youtube_request

def list_videos(max_results=10, page_token=None):
    try:
        # Fetch user's uploaded videos
        url = f"search?part=snippet&forMine=true&type=video&order=date&maxResults={max_results}"
        if page_token:
            url += f"&pageToken={page_token}"
            
        results = make_youtube_request(url)
        items = results.get('items', [])
        
        if not items:
            print("No recent videos found on this channel.")
            return

        print(f"Found recent videos:")
        print("=" * 80)
        
        for item in items:
            snippet = item.get('snippet', {})
            video_id = item.get('id', {}).get('videoId')
            
            print(f"Video ID:    {video_id}")
            print(f"Title:       {snippet.get('title')}")
            print(f"Published:   {snippet.get('publishedAt')}")
            print(f"Description: {snippet.get('description')}")
            print(f"URL:         https://www.youtube.com/watch?v={video_id}")
            print("-" * 80)
            
        next_token = results.get('nextPageToken')
        if next_token:
            print(f"\n[More videos available] To view next page, add: --page-token {next_token}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List recent videos from the authenticated YouTube channel.')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of videos to return (1-50)')
    parser.add_argument('--page-token', type=str, help='Token for the next page of results')
    args = parser.parse_args()
    
    if args.max_results < 1:
        args.max_results = 1
    elif args.max_results > 50:
        args.max_results = 50
        
    list_videos(max_results=args.max_results, page_token=args.page_token)
