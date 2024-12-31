import time
import subprocess
import statistics
import speedtest
import threading
from collections import deque
from ..models.network_stats import NetworkStats
from ..utils.interface import get_preferred_interface, get_interface_ip
from ..utils.config_manager import config_manager
from ..config import DEFAULT_HISTORY_LENGTH
import logging

logger = logging.getLogger('monitor')

class NetworkMonitor:
    def __init__(self):
        self.interface = get_preferred_interface()
        self.interface_ip = get_interface_ip(self.interface)
        self.ping_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)
        self.jitter_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)
        self.packet_loss_history = deque(maxlen=DEFAULT_HISTORY_LENGTH)
        self.last_speed_test = 0
        self.download_speed = 0
        self.upload_speed = 0
        self.is_speed_testing = False
        self.speed_test_thread = None

        logger.info(f"Using interface: {self.interface} ({self.interface_ip}), target host: {config_manager.get_setting('ping_target')}")
        print(f"Using interface: {self.interface} ({self.interface_ip}), target host: {config_manager.get_setting('ping_target')}")
    
    def run_speed_test(self):
        """Start a speed test in a separate thread"""
        if self.is_speed_testing:
            return
            
        def speed_test_worker():
            self.is_speed_testing = True
            try:
                if not self.interface_ip:
                    raise Exception("No valid IP address for interface")
                
                st = speedtest.Speedtest(secure=True)
                st.get_config()
                st.get_best_server()
                
                self.download_speed = st.download() / 1_000_000
                self.upload_speed = st.upload() / 1_000_000
                
                self.last_speed_test = time.time()
                logger.info(f"Speed test completed - Down: {self.download_speed:.1f} Mbps, Up: {self.upload_speed:.1f} Mbps")
            except Exception as e:
                logger.error(f"Speed test failed: {e}")
            finally:
                self.is_speed_testing = False

        self.speed_test_thread = threading.Thread(target=speed_test_worker)
        self.speed_test_thread.daemon = True
        self.speed_test_thread.start()

    def get_stats(self, count=5, ping_interval=0.2) -> NetworkStats:
        """Execute ping command and return network statistics"""
        speed_test_interval = config_manager.get_setting('speed_test_interval') * 60  # Convert minutes to seconds
        if time.time() - self.last_speed_test > speed_test_interval and not self.is_speed_testing:
            self.run_speed_test()
            
        try:
            ping_target = config_manager.get_setting('ping_target')
            cmd = ['ping', ping_target, '-c', str(count), '-i', str(ping_interval), '-I', self.interface]
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
            logger.error(f"Error during ping: {e}")

        return NetworkStats(
            timestamp=time.time(),
            ping_history=self.ping_history,
            jitter_history=self.jitter_history,
            packet_loss_history=self.packet_loss_history,
            speed_test_status=self.is_speed_testing,
            speed_test_timestamp=self.last_speed_test,
            download_speed=self.download_speed,
            upload_speed=self.upload_speed,
            interface=self.interface,
            interface_ip=self.interface_ip,
            ping_target=config_manager.get_setting('ping_target')
        ) 