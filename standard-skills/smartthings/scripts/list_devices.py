#!/usr/bin/env python3
import sys
import argparse
from auth import make_smartthings_request

def list_devices():
    try:
        # Fetch all devices
        results = make_smartthings_request("devices")
        devices = results.get('items', [])
        
        if not devices:
            print("No SmartThings devices found attached to this account.")
            return

        print(f"Found {len(devices)} connected devices:")
        print("=" * 70)
        
        for device in devices:
            print(f"Device ID:    {device.get('deviceId')}")
            print(f"Name:         {device.get('label') or device.get('name')}")
            print(f"Location ID:  {device.get('locationId')}")
            print(f"Room ID:      {device.get('roomId', 'N/A')}")
            
            # Extract main components and capabilities
            components = device.get('components', [])
            capabilities = []
            for comp in components:
                if comp.get('id') == 'main':
                    capabilities = [c.get('id') for c in comp.get('capabilities', [])]
                    break
            
            print(f"Capabilities: {', '.join(capabilities[:10])}{' ...' if len(capabilities) > 10 else ''}")
            print("-" * 70)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='List all connected SmartThings devices.')
    parser.parse_args()
    
    list_devices()
