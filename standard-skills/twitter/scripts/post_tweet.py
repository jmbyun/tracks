#!/usr/bin/env python3
import sys
import argparse
from auth import make_twitter_request

def post_tweet(text, reply_to_id=None):
    try:
        data = {"text": text}
        if reply_to_id:
            data["reply"] = {
                "in_reply_to_tweet_id": str(reply_to_id)
            }
            
        print(f"Publishing tweet...")
        result = make_twitter_request("tweets", method="POST", data=data)
        
        tweet_data = result.get('data', {})
        tweet_id = tweet_data.get('id')
        
        if not tweet_id:
            raise Exception("Failed to get Tweet ID from Twitter API.")
            
        print(f"Successfully published new tweet!")
        print(f"Tweet ID: {tweet_id}")
        print(f"Preview: {tweet_data.get('text')}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Publish a new tweet to X (Twitter).')
    parser.add_argument('text', type=str, help='The text content of the tweet')
    parser.add_argument('--reply-to', type=str, help='If provided, this tweet will reply to the given Tweet ID')
    
    args = parser.parse_args()
    post_tweet(args.text, reply_to_id=args.reply_to)
