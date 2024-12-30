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
        
        # Create hotspot using the simplified command
        print(f"Creating AP hotspot: {self.ap_ssid}")
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', self.interface,
            'ssid', self.ap_ssid,
            'password', self.ap_password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error creating AP hotspot: {result.stderr}")
            return
            
        # Wait for AP to start
        time.sleep(5)
        
        # Check AP status
        print("\nChecking AP status:")
        subprocess.run(['sudo', 'nmcli', 'device', 'show', self.interface])
    
    def configure_wifi(self, ssid: str, password: str) -> bool:
        """Configure WiFi client connection using NetworkManager"""
        print(f"Connecting to WiFi network: {ssid}")
        
        # Stop AP mode
        subprocess.run(['sudo', 'nmcli', 'connection', 'down', 'Hotspot'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # Connect to the new network
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
            'password', password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error connecting to network: {result.stderr}")
            return False
            
        # Wait for connection
        print("Waiting for connection...")
        time.sleep(10)
        
        return self.check_connection()