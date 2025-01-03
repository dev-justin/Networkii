#!/usr/bin/env python3

import argparse
import subprocess
from rich.console import Console
from networkii.utils.config_manager import config_manager
from networkii.utils.network import connect_to_wifi

console = Console()

def show_config():
    """Display current configuration"""
    config = config_manager.get_config()
    console.print("\n[bold cyan]Current Configuration:[/bold cyan]")
    console.print(f"[green]Ping Target:[/green] {config.get('ping_target', 'Not set')}")
    console.print(f"[green]Speed Test Interval:[/green] {config.get('speed_test_interval', 'Not set')} minutes\n")

def update_config(args):
    """Update configuration with new values"""
    current_config = config_manager.get_config()
    changes_made = False

    if args.ping_target is not None:
        current_config['ping_target'] = args.ping_target
        changes_made = True

    if args.speed_test_interval is not None:
        if 5 <= args.speed_test_interval <= 1440:
            current_config['speed_test_interval'] = args.speed_test_interval
            changes_made = True
        else:
            console.print("[red]Error: Speed test interval must be between 5 and 1440 minutes.[/red]")
            return

    if changes_made:
        console.print("[yellow]Updating configuration...[/yellow]")
        config_manager.update_config(current_config)
        console.print("[green]Configuration updated successfully![/green]")
        show_config()
    else:
        console.print("[yellow]No changes specified. Use --help to see available options.[/yellow]")

def wifi_setup(args):
    """Connect to WiFi using provided credentials"""
    if not args.ssid:
        console.print("[red]Error: SSID (--ssid) is required for WiFi connection[/red]")
        return
    if not args.password:
        console.print("[red]Error: Password (--password) is required for WiFi connection[/red]")
        return

    console.print(f"[yellow]Attempting to connect to WiFi network: {args.ssid}[/yellow]")
    connected = connect_to_wifi(args.ssid, args.password)
    if connected:
        console.print(f"[green]Successfully connected to WiFi ({args.ssid})[/green]")
    else:
        console.print(f"[red]Failed to connect to WiFi ({args.ssid})[/red]")

def start_service():
    """Start the networkii service"""
    console.print("[yellow]Starting networkii service...[/yellow]")
    subprocess.run(["sudo", "systemctl", "start", "networkii"])
    console.print("[green]Networkii service started successfully![/green]")

def stop_service():
    """Stop the networkii service"""
    console.print("[yellow]Stopping networkii service...[/yellow]")
    subprocess.run(["sudo", "systemctl", "stop", "networkii"])
    console.print("[green]Networkii service stopped successfully![/green]")

def restart_service():
    """Restart the networkii service"""
    console.print("[yellow]Restarting networkii service...[/yellow]")
    subprocess.run(["sudo", "systemctl", "restart", "networkii"])
    console.print("[green]Networkii service restarted successfully![/green]")

def show_ics_status():
    """Show ICS status"""
    console.print("[yellow]ICS Status:[/yellow]")
    subprocess.run(["sudo", "systemctl", "status", "ics"])

def enable_ics():
    """Enable ICS"""
    console.print("[yellow]Enabling ICS...[/yellow]")
    subprocess.run(["sudo", "systemctl", "enable", "ics"])
    subprocess.run(["sudo", "systemctl", "start", "ics"])
    console.print("[green]ICS enabled and started successfully![/green]")

def disable_ics():
    """Disable ICS"""
    console.print("[yellow]Disabling ICS...[/yellow]")
    subprocess.run(["sudo", "systemctl", "disable", "ics"])
    subprocess.run(["sudo", "systemctl", "stop", "ics"])
    subprocess.run(["sudo", "nmcli", "connection", "down", "usb0"])
    console.print("[green]ICS stopped and disabled successfully![/green]")

def main():
    parser = argparse.ArgumentParser(
        description='Networkii - Network monitoring and configuration tool'
    )
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Basic commands (no arguments needed)
    subparsers.add_parser('show', help='Display current configuration')
    subparsers.add_parser('start', help='Start the networkii service')
    subparsers.add_parser('stop', help='Stop the networkii service')
    subparsers.add_parser('restart', help='Restart the networkii service')
    
    # "set" command with options
    set_parser = subparsers.add_parser('set', help='Update configuration values')
    set_parser.add_argument('--ping', help='Set the ping target (e.g., 1.1.1.1)')
    set_parser.add_argument('--speedtest-interval', type=int, 
                           help='Set speed test interval in minutes (5-1440)')
    
    # "connect" command with required arguments
    connect_parser = subparsers.add_parser('connect', help='Connect to a WiFi network')
    connect_parser.add_argument('ssid', help='WiFi network name')
    connect_parser.add_argument('password', help='WiFi password')

    # "ics" command
    ics_parser = subparsers.add_parser('ics', help='Manage Internet Connection Sharing')
    ics_parser.add_argument('action', nargs='?', choices=['on', 'off'], 
                           help='Turn ICS on or off (leave empty to show status)')

    args = parser.parse_args()

    if args.command == 'show':
        show_config()
    elif args.command == 'set':
        update_config(args)
    elif args.command == 'connect':
        wifi_setup(args)
    elif args.command == 'start':
        start_service()
    elif args.command == 'stop':
        stop_service()
    elif args.command == 'restart':
        restart_service()
    elif args.command == 'ics':
        if args.action == 'on':
            enable_ics()
        elif args.action == 'off':
            disable_ics()
        else:
            show_ics_status()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()