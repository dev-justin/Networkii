import subprocess
import time
import netifaces
import logging
from ..utils.interface import get_preferred_interface

# Set up logging
logging.basicConfig(
    filename='networkii.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('network_manager')

class NetworkManager:
    def __init__(self):
        self.ap_ssid = "NetworkiiAP"
        self.ap_password = "networkii"
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
        print("Setting up AP mode...")
        
        # Create hotspot using the simplified command
        logger.info(f"Creating AP hotspot with SSID: {self.ap_ssid}")
        print(f"Creating AP hotspot: {self.ap_ssid}")
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', self.interface,
            'ssid', self.ap_ssid,
            'password', self.ap_password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Error creating AP hotspot: {result.stderr}"
            logger.error(error_msg)
            print(error_msg)
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
        print(f"Connecting to WiFi network: {ssid}")
        
        # Stop AP mode
        logger.info("Stopping AP mode...")
        subprocess.run(['sudo', 'nmcli', 'connection', 'down', 'Hotspot'], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        
        # Connect to the new network
        logger.info("Connecting to new network...")
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
            'password', password
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Error connecting to network: {result.stderr}"
            logger.error(error_msg)
            print(error_msg)
            return False
            
        # Wait for connection
        logger.info("Waiting for connection to establish...")
        print("Waiting for connection...")
        time.sleep(10)
        
        connection_status = self.check_connection()
        logger.info(f"WiFi configuration {'successful' if connection_status else 'failed'}")
        return connection_status