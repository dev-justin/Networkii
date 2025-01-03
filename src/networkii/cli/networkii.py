#!/usr/bin/env python3

import argparse
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from networkii.utils.config_manager import config_manager
from networkii.utils.network import connect_to_wifi

console = Console()

def show_config():
    """Display current configuration"""
    config = config_manager.get_config()
    
    # Create a beautiful table for configuration
    table = Table(title="Current Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Ping Target", str(config.get('ping_target', 'Not set')))
    table.add_row("Speed Test Interval", f"{config.get('speed_test_interval', 'Not set')} minutes")
    
    console.print()
    console.print(table)
    console.print()

def print_beautiful_help():
    """Display a beautiful help screen"""
    title = Text("🌟 Networkii CLI", style="bold cyan")
    console.print(Panel(title, expand=False))
    console.print()
    
    # Commands table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Command", style="cyan", justify="right")
    table.add_column("Description", style="green")
    table.add_column("Example", style="yellow")
    
    table.add_row(
        "show",
        "Display current configuration",
        "networkii show"
    )
    table.add_row(
        "set",
        "Update configuration values",
        "networkii set --ping-target 1.1.1.1"
    )
    table.add_row(
        "connect",
        "Connect to a WiFi network",
        "networkii connect --ssid MyWiFi --password pass123"
    )
    table.add_row(
        "restart",
        "Restart the networkii service",
        "networkii restart"
    )
    table.add_row(
        "ics",
        "Show ICS status",
        "networkii ics"
    )
    
    console.print(table)
    console.print()
    
    # Options table
    options_table = Table(title="Available Options", show_header=True, header_style="bold magenta")
    options_table.add_column("Option", style="cyan", justify="right")
    options_table.add_column("Description", style="green")
    options_table.add_column("Valid Values", style="yellow")
    
    options_table.add_row(
        "--ping-target",
        "IP address to ping",
        "Any valid IP (e.g., 1.1.1.1)"
    )
    options_table.add_row(
        "--speed-test-interval",
        "Minutes between speed tests",
        "5-1440 minutes"
    )
    options_table.add_row(
        "--ssid",
        "WiFi network name",
        "Your network SSID"
    )
    options_table.add_row(
        "--password",
        "WiFi password",
        "Your network password"
    )
    options_table.add_row(
        "--enable",
        "Enable ICS",
        "networkii ics --enable"
    )
    options_table.add_row(
        "--disable",
        "Disable ICS",
        "networkii ics --disable"
    )

    console.print(options_table)
    console.print()

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
            console.print("[red]Error:[/red] Speed test interval must be between 5 and 1440 minutes.")
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
        console.print("[red]Error:[/red] SSID (--ssid) is required for WiFi connection")
        return
    if not args.password:
        console.print("[red]Error:[/red] Password (--password) is required for WiFi connection")
        return

    console.print(f"[yellow]Attempting to connect to WiFi network:[/yellow] {args.ssid}")
    connected = connect_to_wifi(args.ssid, args.password)
    if connected:
        console.print(f"[green]Successfully connected to WiFi ({args.ssid})[/green]")
    else:
        console.print(f"[red]Failed to connect to WiFi ({args.ssid})[/red]")

def restart_service():
    """Restart the networkii service"""
    console.print("[yellow]Restarting networkii service...[/yellow]")
    subprocess.run(["sudo", "systemctl", "restart", "networkii"])
    console.print("[green]Networkii service restarted successfully![/green]")

def show_ics_status():
    """Show ICS status"""
    console.print("[yellow]Showing ICS status...[/yellow]")
    subprocess.run(["sudo", "systemctl", "status", "ics"])

def enable_ics():
    """Enable ICS"""
    console.print("[yellow]Enabling ICS...[/yellow]")
    subprocess.run(["sudo", "systemctl", "enable", "ics"])
    subprocess.run(["sudo", "systemctl", "start", "ics"])
    console.print("[green]ICS enabled successfully![/green]")

def disable_ics():
    """Disable ICS"""
    console.print("[yellow]Disabling ICS...[/yellow]")
    subprocess.run(["sudo", "systemctl", "disable", "ics"])
    subprocess.run(["sudo", "systemctl", "stop", "ics"])
    console.print("[green]ICS stopped and disabled successfully![/green]")

def main():
    parser = argparse.ArgumentParser(
        description='Networkii Configuration Tool',
        add_help=False  # Disable default help
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

    # Enable ICS
    ics_parser = subparsers.add_parser('ics', help='Show ICS status')
    ics_parser.add_argument('--enable', action='store_true', help='Enable ICS')
    ics_parser.add_argument('--disable', action='store_true', help='Disable ICS')

    args = parser.parse_args()

    if args.command == 'show':
        show_config()
    elif args.command == 'set':
        update_config(args)
    elif args.command == 'connect':
        wifi_setup(args)
    elif args.command == 'restart':
        restart_service()
    elif args.command == 'ics':
        if args.enable:
            enable_ics()
        elif args.disable:
            disable_ics()
        else:
            show_ics_status()
    else:
        print_beautiful_help()

if __name__ == "__main__":
    main()