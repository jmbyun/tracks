#!/usr/bin/env python3
import sys
import argparse
from auth import make_twitter_request

def list_tweets(max_results=10, pagination_token=None):
    try:
        # First we need our own user ID
        me = make_twitter_request("users/me")
        user_id = me.get('data', {}).get('id')
        if not user_id:
            raise Exception("Failed to retrieve authenticated user ID.")
            
        # Fetch user's tweets
        url = f"users/{user_id}/tweets?max_results={max_results}&tweet.fields=created_at,public_metrics,conversation_id"
        if pagination_token:
            url += f"&pagination_token={pagination_token}"
            
        results = make_twitter_request(url)
        tweets = results.get('data', [])
        meta = results.get('meta', {})
        
        if not tweets:
            print("No tweets found on this account.")
            return

        print(f"Found {len(tweets)} recent tweets:")
        print("=" * 70)
        
        for tweet in tweets:
            print(f"Tweet ID:    {tweet.get('id')}")
            print(f"Date:        {tweet.get('created_at')}")
            print(f"Text:\n{tweet.get('text')}\n")
            
            metrics = tweet.get('public_metrics', {})
            print(f"Metrics:   [Replies: {metrics.get('reply_count', 0)}] [Retweets: {metrics.get('retweet_count', 0)}] [Likes: {metrics.get('like_count', 0)}]")
            print("-" * 70)
            
        next_token = meta.get('next_token')
        if next_token:
            print(f"\n[More tweets available] To view next page, add: --pagination-token {next_token}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List recent tweets from the authenticated X (Twitter) account.')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of tweets to return (allowed values: 5-100)')
    parser.add_argument('--pagination-token', type=str, help='Token for the next page of results')
    args = parser.parse_args()
    
    # Twitter requires max_results between 5 and 100
    if args.max_results < 5:
        args.max_results = 5
    elif args.max_results > 100:
        args.max_results = 100
        
    list_tweets(max_results=args.max_results, pagination_token=args.pagination_token)
