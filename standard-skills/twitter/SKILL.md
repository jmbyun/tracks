---
name: twitter
description: Skill for reading profiles, retrieving recent tweets, and publishing new tweets to X (Twitter). Use this when the user asks you to interact with their Twitter account.
---

# X (Twitter) Skill

This skill allows Tracks to act as a Twitter client using the official Twitter V2 API.

## Prerequisites

The authentication is handled automatically by Tracks's built-in OAuth support. Environment variables `TWITTER_CLIENT_ID`, `TWITTER_CLIENT_SECRET`, `TWITTER_OAUTH_TOKEN` and `TWITTER_REFRESH_TOKEN` are securely passed to these scripts via the Agent's runtime environment.

If a script fails with missing credentials or authentication errors, instruct the user to go to the "Connections" page in the App Settings and reconnect the Twitter integration.

## Available Tools

The following scripts are available in the `scripts/` directory:

### 1. View Profile
Retrieves basic user info (name, handle, follower counts, descriptions).
```bash
python scripts/get_profile.py
```

### 2. List Recent Tweets
Retrieves the user's latest tweets, including the text, metrics (likes/retweets), and Tweet ID.
```bash
python scripts/list_tweets.py [--max-results 10]
```

### 3. Publish New Tweet
Posts a new text status to the user's X (Twitter) timeline.
```bash
python scripts/post_tweet.py "Your tweet text here"
```

### 4. Reply to a Tweet
Replies directly to an existing tweet using its Tweet ID.
```bash
python scripts/post_tweet.py "Your reply text here" --reply-to <TWEET_ID>
```

### 5. Search Tweets
Searches the global or recent timeline for tweets matching a specific query string.
```bash
python scripts/search_tweets.py "query text" [--max-results 10]
```

## Usage Guidelines
- **Tokens**: The scripts automatically manage the PKCE refresh tokens transparently.
- **Constraints**: API rate limits apply based on the developer account's Free/Basic tier limits. Ensure you only retrieve what you need.
