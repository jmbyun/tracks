#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
from auth import make_youtube_request

def search_videos(query, max_results=10, page_token=None):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"search?part=snippet&q={encoded_query}&type=video&order=relevance&maxResults={max_results}"
        if page_token:
            url += f"&pageToken={page_token}"
            
        results = make_youtube_request(url)
        items = results.get('items', [])
        
        if not items:
            print(f"No videos found matching query: '{query}'")
            return

        print(f"Search Results for '{query}':")
        print("=" * 80)
        
        for item in items:
            snippet = item.get('snippet', {})
            video_id = item.get('id', {}).get('videoId')
            
            print(f"Video ID:      {video_id}")
            print(f"Channel:       {snippet.get('channelTitle')}")
            print(f"Title:         {snippet.get('title')}")
            print(f"Published At:  {snippet.get('publishedAt')}")
            print(f"Description:   {snippet.get('description')}")
            print(f"URL:           https://www.youtube.com/watch?v={video_id}")
            print("-" * 80)
            
        next_token = results.get('nextPageToken')
        if next_token:
            print(f"\n[More videos available] To view next page, add: --page-token {next_token}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Search YouTube for videos matching a query.')
    parser.add_argument('query', type=str, help='The search query')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of videos to return (1-50)')
    parser.add_argument('--page-token', type=str, help='Token for the next page of results')
    args = parser.parse_args()
    
    if args.max_results < 1:
        args.max_results = 1
    elif args.max_results > 50:
        args.max_results = 50
        
    search_videos(args.query, max_results=args.max_results, page_token=args.page_token)
