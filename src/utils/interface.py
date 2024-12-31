import netifaces
from typing import Optional

def get_preferred_interface() -> str:
    """Get the preferred network interface (usb0 with ICS standard IPv4 if available, otherwise wlan0)"""
    interfaces = netifaces.interfaces()
    
    if 'usb0' in interfaces:
        addrs = netifaces.ifaddresses('usb0')
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                if addr['addr'].startswith('192.168.137.'):
                    return 'usb0'
    
    return 'wlan0'

def get_interface_ip(interface_name: str) -> Optional[str]:
    """Get IP address for the given interface"""
    try:
        addrs = netifaces.ifaddresses(interface_name)
        if netifaces.AF_INET in addrs:
            return addrs[netifaces.AF_INET][0]['addr']
    except Exception as e:
        print(f"Error getting IP for interface {interface_name}: {e}")
    return None 