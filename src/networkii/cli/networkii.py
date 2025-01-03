#!/usr/bin/env python3

import argparse
import subprocess
from networkii.utils.config_manager import config_manager
from networkii.utils.network import connect_to_wifi

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

def wifi_setup(args):
    """Connect to WiFi using provided credentials"""
    if not args.ssid:
        print("Error: SSID (--ssid) is required for WiFi connection")
        return
    if not args.password:
        print("Error: Password (--password) is required for WiFi connection")
        return

    print(f"Attempting to connect to WiFi network: {args.ssid}")
    connected = connect_to_wifi(args.ssid, args.password)
    if connected:
        print(f"Connected to WiFi ({args.ssid})")
    else:
        print(f"Failed to connect to WiFi ({args.ssid})")

def restart_service():
    """Restart the networkii service"""
    print("Restarting networkii service...")
    subprocess.run(["systemctl", "restart", "networkii"])
    print("Networkii service restarted successfully!")

def main():
    parser = argparse.ArgumentParser(
        description='Networkii Configuration Tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # "connect" command
    connect_parser = subparsers.add_parser('connect', help='Connect to WiFi')
    connect_parser.add_argument('--ssid', help="WiFi network name", required=True)
    connect_parser.add_argument('--password', help="WiFi password", required=True)

    # "show" command
    subparsers.add_parser('show', help='Show current configuration')
    
    # "set" command
    set_parser = subparsers.add_parser('set', help='Set configuration values')
    set_parser.add_argument('--ping-target', help='Set the ping target (e.g., 1.1.1.1)')
    set_parser.add_argument('--speed-test-interval', type=int, help='Set speed test interval in minutes (5-1440)')
    
    # "restart" command
    subparsers.add_parser('restart', help='Restart the networkii service')

    args = parser.parse_args()

    if args.command == 'show':
        show_config()
    elif args.command == 'set':
        update_config(args)
    elif args.command == 'connect':
        wifi_setup(args);
    elif args.command == 'restart':
        restart_service()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()