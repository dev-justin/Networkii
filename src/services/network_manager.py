import subprocess
import time
import netifaces
from ..utils.interface import get_preferred_interface

class NetworkManager:
    def __init__(self):
        self.ap_ssid = "Networkii"
        self.ap_password = "networkii"
        self.interface = get_preferred_interface()
        
    def check_connection(self) -> bool:
        """Check if we have a working network connection"""
        try:
            # Check if interface exists and has an IP
            if self.interface not in netifaces.interfaces():
                return False
                
            addrs = netifaces.ifaddresses(self.interface)
            if netifaces.AF_INET not in addrs:
                return False
                
            # Test internet connectivity
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '1.1.1.1'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except:
            return False
    
    def setup_ap_mode(self):
        """Configure and start AP mode using NetworkManager"""
        print("Setting up AP mode...")
        
        # Delete existing AP connection if it exists
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', self.ap_ssid], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # Create new AP connection
        print(f"Creating AP hotspot: {self.ap_ssid}")
        result = subprocess.run([
            'sudo', 'nmcli', 'connection', 'add',
            'type', 'wifi',
            'ifname', self.interface,
            'con-name', self.ap_ssid,
            'autoconnect', 'yes',
            'ssid', self.ap_ssid,
            'mode', 'ap',
            'ipv4.method', 'shared',
            'wifi-sec.key-mgmt', 'wpa-psk',
            'wifi-sec.psk', self.ap_password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating AP: {result.stderr}")
            return
            
        # Activate the connection
        print("Activating AP connection")
        result = subprocess.run([
            'sudo', 'nmcli', 'connection', 'up', self.ap_ssid
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error activating AP: {result.stderr}")
            return
            
        # Wait for AP to start
        time.sleep(5)
        
        # Check AP status
        print("\nChecking AP status:")
        subprocess.run(['sudo', 'nmcli', 'device', 'show', self.interface])
        subprocess.run(['sudo', 'nmcli', 'connection', 'show', self.ap_ssid])
    
    def configure_wifi(self, ssid: str, password: str) -> bool:
        """Configure WiFi client connection using NetworkManager"""
        print(f"Connecting to WiFi network: {ssid}")
        
        # Delete existing AP mode connection
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', self.ap_ssid],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
        
        # Delete existing connection with same SSID if it exists
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid],
                      stdout=subprocess.DEVNULL,
                      stderr=subprocess.DEVNULL)
        
        # Add new connection
        result = subprocess.run([
            'sudo', 'nmcli', 'connection', 'add',
            'type', 'wifi',
            'ifname', self.interface,
            'con-name', ssid,
            'autoconnect', 'yes',
            'ssid', ssid,
            'wifi-sec.key-mgmt', 'wpa-psk',
            'wifi-sec.psk', password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error adding connection: {result.stderr}")
            return False
            
        # Activate the connection
        result = subprocess.run([
            'sudo', 'nmcli', 'connection', 'up', ssid
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error connecting to network: {result.stderr}")
            return False
            
        # Wait for connection
        print("Waiting for connection...")
        time.sleep(10)
        
        return self.check_connection()