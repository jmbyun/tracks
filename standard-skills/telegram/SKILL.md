---
name: telegram
description: Send status messages or notifications to users via Telegram. Use this skill when you need to proactively notify the user about task completion, errors, or important events.
---

# Telegram Messaging

This skill provides a simple way to send messages to the configured users via Telegram.

## Usage

Use the provided `scripts/send.py` script to send messages. It relies on the environment variables `TELEGRAM_BOT_TOKEN` and `TELEGRAM_USER_IDS` to function, which should be set in the environment before execution.

```bash
python scripts/send.py "Your message here"
```

### Examples

**Sending a simple completion message:**
```bash
python scripts/send.py "The data processing task has completed successfully."
```

**Sending a multi-line message (use proper quoting):**
```bash
python scripts/send.py "Task Failed.
Reason: API rate limit exceeded.
Please check the logs for more details."
```

## Setup

Ensure your environment has the required variables. The system should provide these automatically from the vault, but for manual testing they are:
- `TELEGRAM_BOT_TOKEN`: The API token for your Telegram bot
- `TELEGRAM_USER_IDS`: A comma-separated list of Telegram User IDs to send the message to

## Important Notes

- Do not use this for back-and-forth conversational chatting; this is purely for sending one-way notifications or alerts to the user.
- The script uses standard libraries only and requires no external dependencies like `requests`.