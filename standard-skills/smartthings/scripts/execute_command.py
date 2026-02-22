#!/usr/bin/env python3
import sys
import argparse
from auth import make_smartthings_request

def execute_command(device_id, component, capability, command, arguments=None):
    try:
        if arguments is None:
            arguments = []
            
        payload = {
            "commands": [
                {
                    "component": component,
                    "capability": capability,
                    "command": command,
                    "arguments": arguments
                }
            ]
        }
            
        print(f"Sending '{command}' to '{capability}' on device {device_id}...")
        
        result = make_smartthings_request(f"devices/{device_id}/commands", method="POST", data=payload)
        
        cmd_result = result.get('results', [{}])[0].get('status')
        if cmd_result == 'ACCEPTED' or cmd_result == 'COMPLETED':
            print("Command successfully accepted by the device.")
        else:
            print(f"Device responded with status: {cmd_result}")
            print(result)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Send a command to a SmartThings device.')
    parser.add_argument('device_id', type=str, help='The ID of the SmartThings device')
    parser.add_argument('--component', type=str, default='main', help='The device component (usually "main")')
    parser.add_argument('--capability', type=str, required=True, help='The capability class (e.g., "switch", "colorControl")')
    parser.add_argument('--command', type=str, required=True, help='The command to execute (e.g., "on", "off", "setColor")')
    parser.add_argument('--args', type=str, nargs='*', default=[], help='Optional arguments for the command, separated by spaces')
    
    args = parser.parse_args()
    
    # Try to parse numeric arguments intelligently
    parsed_args = []
    for arg in args.args:
        if arg.isdigit():
            parsed_args.append(int(arg))
        else:
            try:
                parsed_args.append(float(arg))
            except ValueError:
                parsed_args.append(arg)
                
    execute_command(args.device_id, args.component, args.capability, args.command, parsed_args)
