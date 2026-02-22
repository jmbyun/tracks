#!/usr/bin/env python3
import sys
import argparse
from auth import make_twitter_request

def get_profile():
    try:
        # Fetch user profile information
        # user.fields=public_metrics,description
        user_info = make_twitter_request("users/me?user.fields=public_metrics,description,created_at")
        
        data = user_info.get('data', {})
        if not data:
            print("Failed to retrieve user data.")
            return

        print("X (Twitter) Profile Information:")
        print("-" * 50)
        print(f"ID:           {data.get('id')}")
        print(f"Name:         {data.get('name')}")
        print(f"Username:     @{data.get('username')}")
        print(f"Description:  {data.get('description', 'N/A')}")
        print(f"Created At:   {data.get('created_at', 'N/A')}")
        
        metrics = data.get('public_metrics', {})
        print("\nMetrics:")
        print(f"Followers:    {metrics.get('followers_count', 0)}")
        print(f"Following:    {metrics.get('following_count', 0)}")
        print(f"Tweets:       {metrics.get('tweet_count', 0)}")
        print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve connected X (Twitter) profile information.')
    parser.parse_args()
    
    get_profile()
