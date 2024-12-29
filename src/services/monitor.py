import time
import subprocess
import statistics
import speedtest
from collections import deque
from ..models.network_stats import NetworkStats
from ..utils.interface import get_preferred_interface, get_interface_ip
from ..config import DEFAULT_TARGET_HOST, DEFAULT_HISTORY_LENGTH, DEFAULT_SPEED_TEST_INTERVAL

class NetworkMonitor:
    def __init__(self, target_host: str = DEFAULT_TARGET_HOST, 
                 history_length: int = DEFAULT_HISTORY_LENGTH, 
                 speed_test_interval: int = DEFAULT_SPEED_TEST_INTERVAL):
        self.target_host = target_host
        self.interface = get_preferred_interface()
        self.interface_ip = get_interface_ip(self.interface)
        self.ping_history = deque(maxlen=history_length)
        self.jitter_history = deque(maxlen=history_length)
        self.packet_loss_history = deque(maxlen=history_length)
        self.speed_test_interval = speed_test_interval * 60  # Convert minutes to seconds
        self.last_speed_test = 0
        self.download_speed = 0
        self.upload_speed = 0

        print(f"Using interface: {self.interface} ({self.interface_ip}), target host: {self.target_host}")
    
    def run_speed_test(self):
        """Run speedtest and update speeds"""
        try:
            if not self.interface_ip:
                raise Exception("No valid IP address for interface")
                
            print(f"Using interface IP for speedtest: {self.interface_ip}")
            st = speedtest.Speedtest(secure=True)
            st.get_config()
            
            print("Finding best server...")
            st.get_best_server()
            
            print("Starting download test...")
            self.download_speed = st.download() / 1_000_000
            
            print("Starting upload test...")
            self.upload_speed = st.upload() / 1_000_000
            
            self.last_speed_test = time.time()
            print(f"Speed test completed - Down: {self.download_speed:.1f} Mbps, Up: {self.upload_speed:.1f} Mbps")
        except Exception as e:
            print(f"Speed test failed: {e}")
    
    def get_stats(self, count=5, ping_interval=0.2) -> NetworkStats:
        """Execute ping command and return network statistics"""
        if time.time() - self.last_speed_test > self.speed_test_interval:
            self.run_speed_test()
            
        try:
            cmd = ['ping', self.target_host, '-c', str(count), '-i', str(ping_interval), '-I', self.interface]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            times = []
            packets_received = 0
            
            for line in result.stdout.splitlines():
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    times.append(float(time_str))
                    packets_received += 1
            
            avg_ping = statistics.mean(times) if times else 0
            jitter = statistics.stdev(times) if len(times) > 1 else 0
            packet_loss = ((count - packets_received) / count) * 100
            
            if avg_ping > 0:
                self.ping_history.append(avg_ping)
            if jitter >= 0:
                self.jitter_history.append(jitter)
            self.packet_loss_history.append(packet_loss)
            
        except Exception as e:
            print(f"Error during ping: {e}")
            
        return NetworkStats(
            timestamp=time.time(),
            ping_history=self.ping_history,
            jitter_history=self.jitter_history,
            packet_loss_history=self.packet_loss_history
        ) 