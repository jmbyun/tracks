#!/usr/bin/env python3
import sys
import argparse
import time
from auth import make_instagram_request, InstagramAuth

def post_media(image_url, caption):
    """
    Publishing media to Instagram is a 2-step process:
    1. Create a media container with the image URL and caption
    2. Publish the container ID
    """
    try:
        # Step 1: Create the media container
        auth = InstagramAuth()
        user_id = auth.user_id
        if not user_id:
            raise ValueError("INSTAGRAM_USER_ID is missing from the vault. Please reconnect the Instagram account.")
            
        print(f"Creating media container for image: {image_url}")
        container_data = make_instagram_request(
            f"{user_id}/media",
            method="POST", 
            data={
                "image_url": image_url,
                "caption": caption
            }
        )
        
        container_id = container_data.get('id')
        if not container_id:
            raise Exception("Failed to get container ID from Instagram API.")
            
        print(f"Container created successfully. ID: {container_id}")
        print("Waiting 10 seconds for Instagram to process the image container...")
        time.sleep(10) # Instagram requires a delay before publishing the container
        
        # Step 2: Publish the container
        print("Publishing container to feed...")
        publish_data = make_instagram_request(
            f"{user_id}/media_publish",
            method="POST",
            data={
                "creation_id": container_id
            }
        )
        
        post_id = publish_data.get('id')
        print(f"Successfully published new media post!")
        print(f"Post ID: {post_id}")
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Publish a new image post to Instagram.')
    parser.add_argument('--image-url', type=str, required=True, help='A publicly accessible URL to the image to post')
    parser.add_argument('--caption', type=str, required=True, help='The text caption for the post')
    
    args = parser.parse_args()
    post_media(args.image_url, args.caption)
