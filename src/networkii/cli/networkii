#!/usr/bin/env python3
"""
Networkii Configuration CLI Tool

Usage Examples:
  1) Show current config:
     $ networkii show

  2) Update configuration:
     $ networkii set --ping-target 1.1.1.1 --speed-test-interval 60
"""

import argparse
from networkii.utils.config_manager import config_manager

def show_config():
    """Display current configuration"""
    config = config_manager.get_config()
    print("\nCurrent Configuration:")
    print("-" * 30)
    print(f"Ping Target          : {config.get('ping_target', 'Not set')}")
    print(f"Speed Test Interval  : {config.get('speed_test_interval', 'Not set')} minutes")
    print("-" * 30)

def update_config(args):
    """Update configuration with new values"""
    current_config = config_manager.get_config()
    changes_made = False

    if args.ping_target is not None:
        current_config['ping_target'] = args.ping_target
        changes_made = True

    if args.speed_test_interval is not None:
        # Validate speed_test_interval to be between 5 and 1440 minutes
        if 5 <= args.speed_test_interval <= 1440:
            current_config['speed_test_interval'] = args.speed_test_interval
            changes_made = True
        else:
            print("Error: Speed test interval must be between 5 and 1440 minutes.")
            return

    if changes_made:
        print("Calling config_manager.update_config...")
        config_manager.update_config(current_config)
        print("Configuration updated successfully!")
        show_config()
    else:
        print("No changes specified. Use --help to see available options.")

def main():
    parser = argparse.ArgumentParser(
        description='Networkii Configuration Tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # "show" command
    subparsers.add_parser('show', help='Show current configuration')
    
    # "set" command
    set_parser = subparsers.add_parser('set', help='Set configuration values')
    set_parser.add_argument('--ping-target', help='Set the ping target (e.g., 1.1.1.1)')
    set_parser.add_argument('--speed-test-interval', type=int,
                           help='Set speed test interval in minutes (5-1440)')

    args = parser.parse_args()

    if args.command == 'show':
        show_config()
    elif args.command == 'set':
        update_config(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()