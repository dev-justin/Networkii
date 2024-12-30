import subprocess
import time
import netifaces
import logging
from ..utils.interface import get_preferred_interface

# Get logger for this module
logger = logging.getLogger('network_manager')

class NetworkManager:
    def __init__(self):
        self.ap_ssid = "Networkii"
        self.interface = get_preferred_interface()
        logger.info(f"NetworkManager initialized with interface: {self.interface}")
        
    def check_connection(self) -> bool:
        """Check if we have a working network connection"""
        try:
            # Check if interface exists and has an IP
            if self.interface not in netifaces.interfaces():
                logger.warning(f"Interface {self.interface} not found")
                return False
                
            addrs = netifaces.ifaddresses(self.interface)
            if netifaces.AF_INET not in addrs:
                logger.warning(f"No IPv4 address found for interface {self.interface}")
                return False
                
            # Test internet connectivity
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '1.1.1.1'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            is_connected = result.returncode == 0
            logger.info(f"Connection check result: {'Connected' if is_connected else 'Disconnected'}")
            return is_connected
        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False
    
    def setup_ap_mode(self):
        """Configure and start AP mode using NetworkManager"""
        logger.info("Setting up AP mode...")
        
        # Create hotspot using the simplified command
        logger.info(f"Creating AP hotspot with SSID: {self.ap_ssid}")
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', self.interface,
            'ssid', self.ap_ssid,
            '802-11-wireless-security.key-mgmt', 'none'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Error creating AP hotspot: {result.stderr}"
            logger.error(error_msg)
            return
            
        # Wait for AP to start
        logger.info("Waiting for AP to start...")
        time.sleep(5)
        
        # Check AP status
        logger.info("Checking AP status...")
        print("\nChecking AP status:")
        status_result = subprocess.run(['sudo', 'nmcli', 'device', 'show', self.interface], capture_output=True, text=True)
        logger.info(f"AP Status:\n{status_result.stdout}")
        subprocess.run(['sudo', 'nmcli', 'device', 'show', self.interface])
    
    def configure_wifi(self, ssid: str, password: str) -> bool:
        """Configure WiFi client connection using NetworkManager"""
        logger.info(f"Attempting to connect to WiFi network: {ssid}")
    
        try:
            # Stop AP mode and delete connection
            logger.info("Stopping AP mode...")
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', 'Hotspot'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            
            # Delete any existing connection with the same SSID to ensure fresh connection
            logger.info(f"Deleting any existing connection for {ssid}")
            subprocess.run(['sudo', 'nmcli', 'connection', 'delete', ssid],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            
            # Connect to the new network
            logger.info("Rescanning WiFi networks...")
            subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.info("Connecting to new network...")
            result = subprocess.run([
                'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                'password', password,
                'ifname', self.interface
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                error_msg = f"Error connecting to network: {result.stderr}"
                logger.error(error_msg)
                print(error_msg)
                return False
            
            # Wait for connection to establish
            logger.info("Waiting for connection to establish...")
            print("Waiting for connection...")
            
            # Check connection status multiple times
            max_attempts = 3
            for attempt in range(max_attempts):
                time.sleep(5)  # Wait between checks
                logger.info(f"Connection check attempt {attempt + 1}/{max_attempts}")
                if self.check_connection():
                    logger.info("Successfully connected to WiFi network")
                    return True
            
            logger.error("Failed to establish connection after multiple attempts")
            return False
            
        except Exception as e:
            logger.error(f"Exception during WiFi configuration: {str(e)}")
            print(f"Error during WiFi configuration: {e}")
            return False
    
    def has_wifi_connection(self) -> bool:
        """Check if we have a WiFi connection (regardless of internet)"""
        try:
            # Check if interface exists and has an IP
            if self.interface not in netifaces.interfaces():
                logger.warning(f"Interface {self.interface} not found")
                return False
                
            addrs = netifaces.ifaddresses(self.interface)
            if netifaces.AF_INET not in addrs:
                logger.warning(f"No IPv4 address found for interface {self.interface}")
                return False
            
            # Check if we have a WiFi connection
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'DEVICE,STATE', 'device'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.splitlines():
                if line.startswith(f"{self.interface}:connected"):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking WiFi connection: {str(e)}")
            return False
    
    def forget_wifi_connection(self):
        """Forget the current WiFi connection"""
        try:
            # Get current connection
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'NAME,DEVICE', 'connection', 'show', '--active'],
                capture_output=True,
                text=True
            )
            
            # Find and delete the connection for our interface
            logger.info(f"Current connection: {result.stdout}")
            for line in result.stdout.splitlines():
                if f":{self.interface}" in line:
                    connection_name = line.split(':')[0]
                    logger.info(f"Forgetting WiFi connection: {connection_name}")
                    subprocess.run(['sudo', 'nmcli', 'connection', 'delete', connection_name],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                    break
            logger.info("Forgetting WiFi connection complete")
        except Exception as e:
            logger.error(f"Error forgetting WiFi connection: {str(e)}")