#!/usr/bin/env python3
import sys
import argparse
from auth import make_youtube_request

def read_comments(video_id, max_results=20, page_token=None):
    try:
        # Fetch top-level comment threads and their replies
        url = f"commentThreads?part=snippet,replies&videoId={video_id}&maxResults={max_results}&order=time"
        if page_token:
            url += f"&pageToken={page_token}"
            
        results = make_youtube_request(url)
        items = results.get('items', [])
        
        if not items:
            print(f"No comments found for video ID: {video_id}")
            return

        print(f"Latest Comments for Video: {video_id}")
        print("=" * 80)
        
        for item in items:
            thread_snippet = item.get('snippet', {})
            top_comment = thread_snippet.get('topLevelComment', {})
            top_snippet = top_comment.get('snippet', {})
            
            comment_id = top_comment.get('id')
            author = top_snippet.get('authorDisplayName')
            text = top_snippet.get('textDisplay')
            likes = top_snippet.get('likeCount', 0)
            published = top_snippet.get('publishedAt')
            reply_count = thread_snippet.get('totalReplyCount', 0)
            
            print(f"Comment ID: {comment_id}")
            print(f"Author:     {author}")
            print(f"Date:       {published} | Likes: {likes} | Replies: {reply_count}")
            print(f"Text:       {text}")
            
            # Print up to 5 replies if they exist
            if reply_count > 0:
                replies_data = item.get('replies', {}).get('comments', [])
                if replies_data:
                    print(f"\n  Replies ({len(replies_data)} shown):")
                    for reply in replies_data:
                        reply_snippet = reply.get('snippet', {})
                        r_author = reply_snippet.get('authorDisplayName')
                        r_text = reply_snippet.get('textDisplay')
                        print(f"  - [{r_author}]: {r_text}")
                        
            print("-" * 80)
            
        next_token = results.get('nextPageToken')
        if next_token:
            print(f"\n[More comments available] To view next page, add: --page-token {next_token}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Read the comments thread of a specific YouTube video.')
    parser.add_argument('video_id', type=str, help='The ID of the YouTube video')
    parser.add_argument('--max-results', type=int, default=20, help='Maximum number of comment threads to return (1-100)')
    parser.add_argument('--page-token', type=str, help='Token for the next page of results')
    args = parser.parse_args()
    
    if args.max_results < 1:
        args.max_results = 1
    elif args.max_results > 100:
        args.max_results = 100
        
    read_comments(args.video_id, max_results=args.max_results, page_token=args.page_token)
