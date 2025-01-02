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
    
def has_wifi_saved(interface) -> bool:
    """Check if we have a WiFi connection present (regardless of Internet)"""
    try:
        # get status and filter for interface and connected
        device_status = subprocess.run(
            ["nmcli", "-f", "DEVICE,STATE", "device", "status"],
            capture_output=True,
            text=True
        )
        if device_status.returncode != 0:
            logger.error(f"Error checking WiFi connection: {device_status.stderr}")
            return False

        for line in device_status.stdout.splitlines():
            if line.strip().startswith("DEVICE") or not line.strip():
                continue

            parts = line.split()
            if len(parts) == 2:
                device, state = parts
                if device == interface:
                    return (state.lower() == "connected")

            return False
    except Exception as e:
        logger.error(f"Error checking WiFi connection: {str(e)}")
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

def start_ap():
    """Start AP mode"""
    try:
        subprocess.run(['nmcli', 'device', 'wifi', 'hotspot', 'ssid', 'networkii', 'password', 'networkii'],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Error starting AP mode: {str(e)}")
        return False    