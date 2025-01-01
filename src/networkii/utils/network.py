import subprocess
import netifaces
from .logger import get_logger
from .config_manager import config_manager

logger = get_logger('network')

def check_connection(interface) -> bool:
    """Check if we have a working network connection on given interface"""
    try:
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET not in addrs:
            logger.error(f"No IPv4 address found for interface {interface}")
            return False
        
        ping_target = config_manager.get_setting('ping_target')
        result = subprocess.run(
            ['ping', '-c', '1', '-W', '1', ping_target, '-I', interface],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Error checking connection: {str(e)}")
        return False
    
def remove_connection(interface) -> bool:
    """Remove NetworkManager connection for given interface"""
    try:
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', interface],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Error removing {interface} connection: {str(e)}")
        return False

def connect_to_wifi(ssid, password, interface="wlan0") -> bool:
    """Connect to WiFi using provided credentials"""
    try:
        subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password, 'ifname', interface],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Error connecting to {ssid}: {str(e)}")
        return False
