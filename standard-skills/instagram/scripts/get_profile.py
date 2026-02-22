#!/usr/bin/env python3
import sys
import argparse
from auth import make_instagram_request

def get_profile():
    try:
        # Fetch user profile information (Instagram Graph API syntax)
        user_info = make_instagram_request("me?fields=id,username,account_type,media_count")
        
        print("Instagram Profile Information:")
        print("-" * 50)
        print(f"ID:           {user_info.get('id')}")
        print(f"Username:     {user_info.get('username')}")
        print(f"Account Type: {user_info.get('account_type')}")
        print(f"Media Count:  {user_info.get('media_count')}")
        print("-" * 50)
        
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Retrieve connected Instagram profile information.')
    parser.parse_args()
    
    get_profile()
