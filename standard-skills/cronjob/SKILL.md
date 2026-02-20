---
name: cronjob
description: Manage scheduled tasks using Tracks' custom python-based crontab clone. This skill allows you to add, edit, or remove cronjobs that will trigger tasks for the agent at specific times by directly editing a text file.
---

# Cronjob Manager

This skill helps you manage scheduled tasks using a custom, pure Python `crontab` clone reading from a simple text file. When a scheduled time is reached, the system executes a background worker that triggers an agent task with the `[CRONJOB]` prefix, followed by your instructions.

The custom crontab reads from: `$AGENT_HOME_PATH/crontabs.txt`

## The Execution Command

Whenever you create a new cronjob, the command MUST use the `cronjob_worker.py` script. The standard command structure to append to `crontabs.txt` is:

```bash
cd /app && /usr/local/bin/python /app/tracks/services/cronjob_worker.py "<Task Instructions>"
```

### Important Command Rules
1. Always `cd` to `/app` (or the installation path).
2. Use the absolute path to python `/usr/local/bin/python`.
3. Pass the specific instruction string as the first argument, enclosed in quotes.

## Checking Existing Cronjobs

To see the currently scheduled tasks, just read the file:
```bash
cat $AGENT_HOME_PATH/crontabs.txt
```
*Note: If the file does not exist, there are no cronjobs.*

## Creating or Modifying Cronjobs

To add a new cronjob, append a new line to `$AGENT_HOME_PATH/crontabs.txt` using the standard cron syntax format. 

### Example: Adding a daily task (at 08:00)

```bash
echo "0 8 * * * cd /app && /usr/local/bin/python /app/tracks/services/cronjob_worker.py \"Send the daily system report\"" >> $AGENT_HOME_PATH/crontabs.txt
```

### Example: Adding a task that runs every 15 minutes

```bash
echo "*/15 * * * * cd /app && /usr/local/bin/python /app/tracks/services/cronjob_worker.py \"Check server health\"" >> $AGENT_HOME_PATH/crontabs.txt
```

## Deleting a Cronjob

To delete a specific cronjob or all cronjobs, just use standard file manipulation tools (like `grep -v`, `sed`, or text replacement) on `$AGENT_HOME_PATH/crontabs.txt`. To remove all cronjobs, you can optionally just empty the file:

```bash
> $AGENT_HOME_PATH/crontabs.txt
```

## Cron Expression Guide

```
* * * * * command
| | | | |
| | | | +- Day of week (0-7) (Sunday=0 or 7)
| | | +--- Month (1-12)
| | +----- Day of month (1-31)
| +------- Hour (0-23)
+--------- Minute (0-59)
```

Example intervals:
- `30 * * * *` = Every hour at 30 minutes past
- `0 12 * * *` = Daily at noon
- `0 0 * * 1` = Every Monday at midnight

