#!/usr/bin/env python3
import sys
import argparse
import urllib.parse
from auth import make_twitter_request

def search_tweets(query, max_results=10, pagination_token=None):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"tweets/search/recent?query={encoded_query}&max_results={max_results}&tweet.fields=created_at,public_metrics,author_id"
        if pagination_token:
            url += f"&next_token={pagination_token}"
            
        results = make_twitter_request(url)
        tweets = results.get('data', [])
        meta = results.get('meta', {})
        
        if not tweets:
            print(f"No recent tweets found for query: '{query}'")
            return

        print(f"Found {len(tweets)} tweets matching '{query}':")
        print("=" * 70)
        
        for tweet in tweets:
            print(f"Tweet ID:    {tweet.get('id')}")
            print(f"Author ID:   {tweet.get('author_id')}")
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
    parser = argparse.ArgumentParser(description='Search for recent tweets on X (Twitter).')
    parser.add_argument('query', type=str, help='The search query (e.g., "AI OR #MachineLearning")')
    parser.add_argument('--max-results', type=int, default=10, help='Maximum number of tweets to return (10-100)')
    parser.add_argument('--pagination-token', type=str, help='Token for the next page of results')
    args = parser.parse_args()
    
    if args.max_results < 10:
        args.max_results = 10
    elif args.max_results > 100:
        args.max_results = 100
        
    search_tweets(args.query, max_results=args.max_results, pagination_token=args.pagination_token)
