import subprocess
import time
import netifaces
import logging
from ..utils.interface import get_preferred_interface

# Get logger for this module
logger = logging.getLogger('network_manager')

class NetworkManager:
    AP_SSID = "networkii"
    AP_PASSWORD = "networkii"
    INTERFACE = "wlan0"
    
    def __init__(self):
        logger.debug(f"NetworkManager initialized with interface: {self.INTERFACE}")
        
    # Checks if we have a valid connection by checking if we have an IPv4 address and if we can ping 1.1.1.1
    def check_connection(self) -> bool:
        """Check if we have a working network connection"""
        
        try:
            # Check if interface exists and has an IP
            preferred_interface = get_preferred_interface()
            if preferred_interface not in netifaces.interfaces():
                logger.error(f"Interface {preferred_interface} not found")
                return False
                
            addrs = netifaces.ifaddresses(preferred_interface)
            if netifaces.AF_INET not in addrs:
                logger.error(f"No IPv4 address found for interface {preferred_interface}")
                return False
                
            # Test internet connectivity
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '1', '1.1.1.1'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking connection: {str(e)}")
            return False
    
    def setup_ap_mode(self):
        """Configure and start AP mode using NetworkManager"""
        
        # Create hotspot
        logger.info(f"Creating AP hotspot with SSID: {self.AP_SSID}")
        result = subprocess.run([
            'sudo', 'nmcli', 'device', 'wifi', 'hotspot',
            'ifname', self.INTERFACE,
            'ssid', self.AP_SSID,
            'password', self.AP_PASSWORD
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            error_msg = f"Error creating AP hotspot: {result.stderr}"
            logger.error(error_msg)
            return
            
        logger.debug("AP hotspot created successfully, waiting for startup")
        time.sleep(3)
    
    def configure_wifi(self, ssid: str, password: str) -> bool:
        """Configure WiFi client connection using NetworkManager"""
    
        try:
            # 1. Tear down AP so we have access to the interface
            logger.debug("Tearing down AP mode...")
            result = subprocess.run(['sudo', 'nmcli', 'connection', 'delete', 'Hotspot'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            
            if result.returncode != 0:
                logger.error(f"Error tearing down AP mode: {result.stderr}")
                return False
            
            # 2. Rescan WiFi networks
            logger.debug("Rescanning WiFi networks...")
            subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            
            # 3. List available networks for logger
            available_networks = subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'list'],
                         stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL)
            logger.debug(f"Available networks: {available_networks.stdout}")
            
            # 4. Attempt to connect to the new network
            logger.info("Attempting to connect to new network...")
            result = subprocess.run([
                'sudo', 'nmcli', 'device', 'wifi', 'connect', ssid,
                'password', password,
                'ifname', self.INTERFACE
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error connecting to network: {result.stderr}")
                self.setup_ap_mode()
                return False
                
            # 5. Check connection status multiple times
            logger.debug("Waiting for connection to establish...")
            max_attempts = 3
            connection_successful = False
            for attempt in range(max_attempts):
                logger.debug(f"Connection check attempt {attempt + 1}/{max_attempts}")
                time.sleep(2)  # Wait between checks
                if self.check_connection():
                    connection_successful = True
                    break
            
            if not connection_successful:
                logger.error("Failed to establish connection after multiple attempts")
                self.setup_ap_mode()
                return False
            
            logger.info("Successfully connected to WiFi network")
            return True
            
        except Exception as e:
            logger.error(f"Exception during WiFi configuration: {str(e)}")
            self.setup_ap_mode()
            return False
    
    def has_wifi_connection(self) -> bool:
        """Check if we have a WiFi connection (regardless of internet)"""
        try:
            # Check if interface exists and has an IP
            if self.INTERFACE not in netifaces.interfaces():
                logger.error(f"Interface {self.INTERFACE} not found")
                return False
                
            addrs = netifaces.ifaddresses(self.INTERFACE)
            if netifaces.AF_INET not in addrs:
                logger.error(f"No IPv4 address found for interface {self.INTERFACE}")
                return False
            
            # Check if we have a WiFi connection
            result = subprocess.run(
                ['nmcli', '-t', '-f', 'DEVICE,STATE', 'device'],
                capture_output=True,
                text=True
            )
            
            for line in result.stdout.splitlines():
                if line.startswith(f"{self.INTERFACE}:connected"):
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
            logger.debug(f"Current connection: {result.stdout}")
            for line in result.stdout.splitlines():
                if f":{self.INTERFACE}" in line:
                    connection_name = line.split(':')[0]
                    logger.info(f"Forgetting WiFi connection: {connection_name}")
                    subprocess.run(['sudo', 'nmcli', 'connection', 'delete', connection_name],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                    break
            logger.debug("Forgetting WiFi connection complete")
        except Exception as e:
            logger.error(f"Error forgetting WiFi connection: {str(e)}")