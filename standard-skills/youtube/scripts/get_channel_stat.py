#!/usr/bin/env python3
import sys
import argparse
from auth import make_youtube_request

def get_channel_stat():
    try:
        # Fetch own channel stats
        results = make_youtube_request("channels?part=statistics,snippet&mine=true")
        items = results.get('items', [])
        
        if not items:
            print("No YouTube channel found associated with this account.")
            return

        channel = items[0]
        snippet = channel.get('snippet', {})
        statistics = channel.get('statistics', {})
        
        print("YouTube Channel Information:")
        print("=" * 50)
        print(f"Channel ID:    {channel.get('id')}")
        print(f"Title:         {snippet.get('title')}")
        print(f"Description:   {snippet.get('description', 'N/A')}")
        print(f"Published At:  {snippet.get('publishedAt')}")
        
        print("\nStatistics:")
        print(f"Subscribers:   {statistics.get('subscriberCount', 0)}")
        print(f"Total Views:   {statistics.get('viewCount', 0)}")
        print(f"Video Count:   {statistics.get('videoCount', 0)}")
        print("=" * 50)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get statistics for the authenticated YouTube channel.')
    parser.parse_args()
    
    get_channel_stat()
