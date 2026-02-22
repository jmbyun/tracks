---
name: youtube
description: Skill for reading channel metrics, listing videos, searching, and managing comments on YouTube. Use this when the user asks you to interact with their YouTube account.
---

# YouTube Skill

This skill allows Tracks to act as a YouTube client using the official YouTube Data API v3.

## Prerequisites

The authentication is handled automatically by Tracks's built-in OAuth support. Environment variables `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_OAUTH_TOKEN` and `YOUTUBE_REFRESH_TOKEN` are securely passed to these scripts via the Agent's runtime environment.

If a script fails with missing credentials or authentication errors, instruct the user to go to the "Connections" page in the App Settings and reconnect the YouTube integration.

## Available Tools

The following scripts are available in the `scripts/` directory:

### 1. View Channel Statistics
Retrieves statistics for the authenticated user's own channel (subscribers, views, video count).
```bash
python scripts/get_channel_stat.py
```

### 2. List Your Videos
Retrieves the recent video uploads from the user's channel.
```bash
python scripts/list_videos.py [--max-results 10]
```

### 3. Search Videos
Searches YouTube globally for videos matching a specific keyword query.
```bash
python scripts/search_videos.py "my search query" [--max-results 10]
```

### 4. Read Comments
Reads a video's top-level comments and existing reply threads. You need the Video ID to use this.
```bash
python scripts/read_comments.py <VIDEO_ID> [--max-results 20]
```

### 5. Reply to Comment
Posts a reply specifically directed at a top-level parent comment. You must use `read_comments.py` to get the target `Comment ID`.
```bash
python scripts/reply_comment.py <COMMENT_ID> "Your reply text here"
```

## Usage Guidelines
- **Tokens**: The scripts automatically manage the OAuth refresh tokens transparently.
- **Constraints**: Be mindful of your API Quota limits; do not make unnecessary API calls.
