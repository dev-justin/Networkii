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
            ["sudo", "nmcli", "-f", "DEVICE,STATE,CONNECTION", "device", "status"],
            capture_output=True,
            text=True
        )

        for line in device_status.stdout.splitlines():
            if line.strip().startswith("DEVICE") or not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 3:  # Changed to >= 3 in case there are spaces in connection names
                device, state, connection = parts[0], parts[1], ' '.join(parts[2:])
                if device == interface and connection != "Hotspot":
                    logger.debug(f"Device: {device}, State: {state}, Connection: {connection}")
                    return (state.lower() == "connected")
        
        return False  # Only return False after checking all lines
    except Exception as e:
        logger.error(f"Error checking WiFi connection: {str(e)}")
        return False

def remove_connection(connection_name) -> bool:
    """Remove NetworkManager connection for given interface"""
    try:
        subprocess.run(['sudo', 'nmcli', 'connection', 'delete', connection_name],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        logger.error(f"Error removing {connection_name} connection: {str(e)}")
        return False
    

def rescan_wifi() -> bool:
    """Rescan WiFi for new networks"""
    try:
        result = subprocess.run(['sudo', 'nmcli', 'device', 'wifi', 'rescan'],
                              capture_output=True,
                              text=True)
        if result.returncode != 0:
            logger.error(f"WiFi rescan failed: {result.stderr}")
            return False
        return True
    except Exception as e:
        logger.error(f"Error rescanning WiFi: {str(e)}")
        return False

def connect_to_wifi(ssid, password) -> bool:
    """Connect to WiFi using provided credentials"""
    try:
        rescan_wifi()
        result = subprocess.run(
            ['sudo', 'nmcli', 'device', 'wifi', 'connect', ssid, 'password', password],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Failed to connect to {ssid}: {error_msg}")
            return False
            
        if "successfully activated" in result.stdout:
            logger.info(f"Successfully connected to {ssid}")
            return True
            
        logger.error(f"Unexpected output when connecting to {ssid}: {result.stdout}")
        return False
        
    except Exception as e:
        logger.error(f"Error connecting to {ssid}: {str(e)}")
        return False

def start_ap() -> bool:
    """Start AP mode"""
    logger.info("Starting AP")
    try:
        result = subprocess.run(
            ['sudo', 'nmcli', 'device', 'wifi', 'hotspot', 'ssid', 'networkii', 'password', 'networkii'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            error_msg = result.stderr.strip() or result.stdout.strip()
            logger.error(f"Failed to start AP mode: {error_msg}")
            return False
            
        if "successfully activated" in result.stdout:
            logger.info("AP mode started successfully")
            return True
            
        logger.error(f"Unexpected output when starting AP mode: {result.stdout}")
        return False
        
    except Exception as e:
        logger.error(f"Error starting AP mode: {str(e)}")
        return False    