---
name: instagram
description: Skill for reading profiles, retrieving posts, reading/replying to comments, and publishing new media on Instagram. Use this when the user asks you to interact with their Instagram account.
---

# Instagram Skill

This skill allows Tracks to act as a fully-featured Instagram client using the official Instagram Graph API.

## Prerequisites

The authentication is handled automatically by Tracks's built-in OAuth support. Environment variables `INSTAGRAM_CLIENT_ID`, `INSTAGRAM_CLIENT_SECRET`, `INSTAGRAM_OAUTH_TOKEN` and `INSTAGRAM_USER_ID` are securely passed to these scripts via the Agent's runtime environment.

If a script fails with missing credentials or authentication errors, instruct the user to go to the "Connections" page in the App Settings and reconnect the Instagram integration.

## Available Tools

The following scripts are available in the `scripts/` directory:

### 1. View Profile
Retrieves basic user info (username, total media count).
```bash
python scripts/get_profile.py
```

### 2. List Recent Posts
Retrieves the user's latest posts, including the caption, images, and Post ID.
```bash
python scripts/list_media.py [--limit 10]
```

### 3. Read Comments
Retrieves comments and nested replies on a specific post. You need the Post ID from the list tool.
```bash
python scripts/comments.py list <POST_ID>
```

### 4. Reply to a Comment
Replies directly to a user's comment on a post. You need the Comment ID from the list tool.
```bash
python scripts/comments.py reply <COMMENT_ID> "Your text reply here"
```

### 5. Publish New Media
Posts a new image and caption to the user's Instagram feed. Note: The URL must be publicly accessible on the internet for Instagram to download it.
```bash
python scripts/publish_media.py --image-url "https://example.com/image.jpg" --caption "Hello world!"
```

## Usage Guidelines
- **Publishing requires public images:** The `publish_media.py` script tells Instagram to fetch the image from a URL. You cannot post local files on the computer directly; they must be hosted somewhere accessible by Instagram.
- **Tokens**: The skills automatically refresh the 60-day token.
