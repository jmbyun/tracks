---
name: smartthings
description: Skill for listing, reading status, and executing commands on SmartThings IoT devices. Use this when the user asks you to interact with their smart home.
---

# SmartThings Skill

This skill allows Tracks to interact with the user's connected Samsung SmartThings devices using the official SmartThings REST API.

## Prerequisites

The authentication is handled automatically by Tracks's built-in OAuth support. Environment variables `SMARTTHINGS_CLIENT_ID`, `SMARTTHINGS_CLIENT_SECRET`, `SMARTTHINGS_OAUTH_TOKEN` and `SMARTTHINGS_REFRESH_TOKEN` are securely passed to these scripts via the Agent's runtime environment.

If a script fails with missing credentials or authentication errors, instruct the user to go to the "Connections" page in the App Settings and reconnect the SmartThings integration.

## Available Tools

The following scripts are available in the `scripts/` directory:

### 1. List Devices
Retrieves all SmartThings devices connected to the user's account, including their Device IDs, Location IDs, and Capabilities. You need the Device ID to use the other tools.
```bash
python scripts/list_devices.py
```

### 2. Get Device Status
Retrieves the real-time status of a specific device (e.g., whether a switch is on/off, what color a light is, or the current temperature reading). Use the Device ID obtained from `list_devices.py`.
```bash
python scripts/get_device_status.py <DEVICE_ID>
```

### 3. Execute Command
Sends a command to a device to change its state. You must specify the component (usually "main"), the capability class (e.g., "switch", "colorControl"), and the command (e.g., "on", "off", "setColor").
```bash
python scripts/execute_command.py <DEVICE_ID> --capability switch --command on
python scripts/execute_command.py <DEVICE_ID> --capability switchLevel --command setLevel --args 50
python scripts/execute_command.py <DEVICE_ID> --capability colorControl --command setColor --args '{"hue": 50, "saturation": 100}'
```

## Usage Guidelines
- **Tokens**: The scripts automatically manage the OAuth refresh tokens transparently.
- **Commands vs Statuses**: To check if a command worked, it's best to call `get_device_status.py` a few seconds after `execute_command.py`.
