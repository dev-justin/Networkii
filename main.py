import time
import subprocess
import statistics
import argparse
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from collections import deque

@dataclass
class NetworkStats:
    ping: float
    jitter: float
    packet_loss: float
    min_ping: float
    max_ping: float
    avg_ping: float
    min_jitter: float
    max_jitter: float
    avg_jitter: float
    min_loss: float
    max_loss: float
    avg_loss: float
    timestamp: float

class NetworkMonitor:
    def __init__(self, target_host: str = "1.1.1.1"):
        self.target_host = target_host
        self.ping_history = deque(maxlen=500)
        self.jitter_history = deque(maxlen=500)
        self.packet_loss_history = deque(maxlen=500)
        
    def update_history(self, ping: float, jitter: float, packet_loss: float):
        """Update history and calculate statistics for all metrics"""
        if ping > 0:
            self.ping_history.append(ping)
        if jitter >= 0:
            self.jitter_history.append(jitter)
        self.packet_loss_history.append(packet_loss)
        
        # Calculate stats for ping
        ping_stats = (
            min(self.ping_history) if self.ping_history else 0,
            max(self.ping_history) if self.ping_history else 0,
            sum(self.ping_history) / len(self.ping_history) if self.ping_history else 0
        )
        
        # Calculate stats for jitter
        jitter_stats = (
            min(self.jitter_history) if self.jitter_history else 0,
            max(self.jitter_history) if self.jitter_history else 0,
            sum(self.jitter_history) / len(self.jitter_history) if self.jitter_history else 0
        )
        
        # Calculate stats for packet loss
        loss_stats = (
            min(self.packet_loss_history) if self.packet_loss_history else 0,
            max(self.packet_loss_history) if self.packet_loss_history else 0,
            sum(self.packet_loss_history) / len(self.packet_loss_history) if self.packet_loss_history else 0
        )
        
        return ping_stats, jitter_stats, loss_stats
        
    def get_stats(self, count=3) -> NetworkStats:
        """Execute ping command and return network statistics"""
        try:
            cmd = ['ping', '-c', str(count), self.target_host]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Initialize variables
            times = []
            packets_received = 0
            
            # Parse the ping output
            for line in result.stdout.splitlines():
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    times.append(float(time_str))
                    packets_received += 1
            
            # Calculate packet loss percentage
            packet_loss = ((count - packets_received) / count) * 100
            
            # Calculate current ping and jitter
            if times:
                avg_ping = sum(times) / len(times)
                jitter = statistics.stdev(times) if len(times) > 1 else 0
            else:
                avg_ping = 0
                jitter = 0
            
            # Update history and get historical stats
            ping_stats, jitter_stats, loss_stats = self.update_history(avg_ping, jitter, packet_loss)
            
            return NetworkStats(
                ping=avg_ping,
                jitter=jitter,
                packet_loss=packet_loss,
                min_ping=ping_stats[0],
                max_ping=ping_stats[1],
                avg_ping=ping_stats[2],
                min_jitter=jitter_stats[0],
                max_jitter=jitter_stats[1],
                avg_jitter=jitter_stats[2],
                min_loss=loss_stats[0],
                max_loss=loss_stats[1],
                avg_loss=loss_stats[2],
                timestamp=time.time()
            )
            
        except Exception as e:
            print(f"Error during ping: {e}")
            return NetworkStats(
                ping=0, jitter=0, packet_loss=100,
                min_ping=0, max_ping=0, avg_ping=0,
                timestamp=time.time()
            )

class Display:
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        
        if not test_mode:
            try:
                import st7789  # Changed from ST7789 to lowercase
                self.disp = st7789.ST7789(
                    port=0,
                    cs=0,  # Changed from 1 to 0
                    dc=9,
                    backlight=13,
                    rotation=270,
                    spi_speed_hz=80 * 1000 * 1000,
                    mode=3
                )
            except ImportError as e:
                print(f"Error importing st7789: {e}")
                print("Running in test mode instead")
                self.test_mode = True
            except FileNotFoundError as e:
                print("Error: SPI device not found. Are SPI permissions set correctly?")
                print("Try: sudo raspi-config")
                print("Navigate to: Interface Options -> SPI -> Enable")
                self.test_mode = True
        
        # Display dimensions
        self.width = 240
        self.height = 320
        
        # Create initial black canvas
        self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        # Try to load a font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            self.font = ImageFont.load_default()

    def update(self, stats: NetworkStats):
        """Update the display with network metrics"""
        # Clear the image
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        
        # Draw title and last update time
        self.draw.text((10, 10), "Network Monitor", font=self.font, fill=(255, 255, 255))
        last_update = time.strftime('%H:%M:%S', time.localtime(stats.timestamp))
        self.draw.text((10, 35), f"Last Update: {last_update}", font=self.font, fill=(255, 255, 255))
        
        # Draw current metrics
        y_offset = 70  # Adjusted to make room for timestamp
        self.draw.text((10, y_offset), f"Ping: {stats.ping:.1f} ms", font=self.font, fill=(255, 255, 255))
        self.draw.text((10, y_offset + 40), f"Jitter: {stats.jitter:.1f} ms", font=self.font, fill=(255, 255, 255))
        self.draw.text((10, y_offset + 80), f"Packet Loss: {stats.packet_loss}%", font=self.font, fill=(255, 255, 255))
        
        # Draw historical stats
        y_offset += 120
        self.draw.text((10, y_offset), "Historical Stats:", font=self.font, fill=(255, 255, 255))
        y_offset += 30
        
        # Ping history
        self.draw.text((10, y_offset), "Ping (min/max/avg):", font=self.font, fill=(255, 255, 255))
        self.draw.text((10, y_offset + 25), f"{stats.min_ping:.1f}/{stats.max_ping:.1f}/{stats.avg_ping:.1f} ms", font=self.font, fill=(255, 255, 255))
        
        # Jitter history
        self.draw.text((10, y_offset + 50), "Jitter (min/max/avg):", font=self.font, fill=(255, 255, 255))
        self.draw.text((10, y_offset + 75), f"{stats.min_jitter:.1f}/{stats.max_jitter:.1f}/{stats.avg_jitter:.1f} ms", font=self.font, fill=(255, 255, 255))
        
        # Packet loss history
        self.draw.text((10, y_offset + 100), "Loss % (min/max/avg):", font=self.font, fill=(255, 255, 255))
        self.draw.text((10, y_offset + 125), f"{stats.min_loss:.1f}/{stats.max_loss:.1f}/{stats.avg_loss:.1f}%", font=self.font, fill=(255, 255, 255))
        
        if self.test_mode:
            # Clear display
            print("\033c", end="")
            print("=== Network Monitor Stats ===")
            print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stats.timestamp))}")
            print("-" * 30)
            print(f"Ping:        {stats.ping:.1f} ms")
            print(f"Jitter:      {stats.jitter:.1f} ms")
            print(f"Packet Loss: {stats.packet_loss}%")
            print("-" * 30)
            print("Historical Stats:")
            print(f"Ping min/max/avg:  {stats.min_ping:.1f}/{stats.max_ping:.1f}/{stats.avg_ping:.1f} ms")
            print(f"Jitter min/max/avg: {stats.min_jitter:.1f}/{stats.max_jitter:.1f}/{stats.avg_jitter:.1f} ms")
            print(f"Loss % min/max/avg: {stats.min_loss:.1f}/{stats.max_loss:.1f}/{stats.avg_loss:.1f}%")
            print("-" * 30)
        else:
            self.disp.display(self.image)

def main():
    parser = argparse.ArgumentParser(description='Network Monitor')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no physical display)')
    parser.add_argument('--host', default='1.1.1.1', help='Target host to ping (default: 1.1.1.1)')
    parser.add_argument('--interval', type=float, default=1.0, help='Update interval in seconds (default: 1.0)')
    args = parser.parse_args()

    network_monitor = NetworkMonitor(target_host=args.host)
    display = Display(test_mode=args.test)

    try:
        while True:
            stats = network_monitor.get_stats()
            display.update(stats)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
