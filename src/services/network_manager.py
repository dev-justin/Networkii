import subprocess
import time
import netifaces
from ..utils.interface import get_preferred_interface
import os

class NetworkManager:
    def __init__(self):
        self.ap_ssid = "NetworkiiAP"
        self.ap_config_path = "/etc/hostapd/hostapd.conf"
        self.network_config_path = "/etc/systemd/network/wlan0.network"
        self.wpa_config_path = "/etc/wpa_supplicant/wpa_supplicant.conf"
        
    def check_connection(self) -> bool:
        """Check if we have a working network connection"""
        interface = get_preferred_interface()
        
        # Check if interface exists and has an IP
        if interface not in netifaces.interfaces():
            return False
            
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET not in addrs:
            return False
            
        # Test internet connectivity
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', '1.1.1.1'],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return result.returncode == 0
        except:
            return False
    
    def setup_ap_mode(self):
        """Configure and start AP mode"""
        print("Stopping network services")
        
        # Stop network services
        subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'])
        subprocess.run(['sudo', 'systemctl', 'stop', 'systemd-networkd'])
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.network_config_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.ap_config_path), exist_ok=True)
        
        # Configure network
        network_config = """
[Match]
Name=wlan0

[Network]
Address=192.168.4.1/24
DHCPServer=yes

[DHCPServer]
PoolOffset=2
PoolSize=18
EmitDNS=yes
DNS=1.1.1.1
"""
        with open(self.network_config_path, 'w') as f:
            f.write(network_config)
        
        # Configure hostapd
        ap_config = f"""
interface=wlan0
driver=nl80211
ssid={self.ap_ssid}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=networkii
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
        with open(self.ap_config_path, 'w') as f:
            f.write(ap_config)
            
        # Unmask and enable hostapd
        print("Configuring hostapd service")
        subprocess.run(['sudo', 'systemctl', 'unmask', 'hostapd'])
        subprocess.run(['sudo', 'systemctl', 'enable', 'hostapd'])
            
        # Start AP services
        print("Starting AP services")
        subprocess.run(['sudo', 'systemctl', 'start', 'systemd-networkd'])
        subprocess.run(['sudo', 'systemctl', 'start', 'hostapd'])
        
        # Wait a bit for services to start
        time.sleep(5)
        
        # Check if hostapd is running
        result = subprocess.run(['sudo', 'systemctl', 'is-active', 'hostapd'], 
                              capture_output=True, text=True)
        if result.stdout.strip() != 'active':
            print("Warning: hostapd service failed to start")
            print("Checking service status...")
            subprocess.run(['sudo', 'systemctl', 'status', 'hostapd'])
    
    def configure_wifi(self, ssid: str, password: str) -> bool:
        """Configure WiFi with provided credentials"""
        wpa_config = f"""
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=US

network={{
    ssid="{ssid}"
    psk="{password}"
    key_mgmt=WPA-PSK
}}
"""
        try:
            with open(self.wpa_config_path, 'w') as f:
                f.write(wpa_config)
                
            # Restart networking
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'])
            subprocess.run(['sudo', 'systemctl', 'restart', 'systemd-networkd'])
            subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'])
            
            # Wait for connection
            time.sleep(10)
            return self.check_connection()
        except:
            return False