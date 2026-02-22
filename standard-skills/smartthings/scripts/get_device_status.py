#!/usr/bin/env python3
import sys
import argparse
from auth import make_smartthings_request

def get_device_status(device_id):
    try:
        # Fetch status for the 'main' component
        status_data = make_smartthings_request(f"devices/{device_id}/status")
        components = status_data.get('components', {})
        main_component = components.get('main', {})
        
        if not main_component:
            print(f"Failed to retrieve status for device {device_id}.")
            return

        print(f"Status for Device ID: {device_id}")
        print("=" * 60)
        
        # Iterate through common capabilities and print their active values
        for capability, attributes in main_component.items():
            for attr_name, attr_data in attributes.items():
                val = attr_data.get('value')
                unit = attr_data.get('unit', '')
                if val is not None:
                    # SmartThings returns heavily nested statuses. Flatten them nicely.
                    print(f"- {capability}.{attr_name}: {val}{unit}")
                    
        print("-" * 60)
            
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Get the real-time status of a SmartThings device.')
    parser.add_argument('device_id', type=str, help='The ID of the SmartThings device')
    args = parser.parse_args()
    
    get_device_status(args.device_id)
