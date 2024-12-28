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
        
        # Display dimensions
        self.width = 320
        self.height = 240
        
        # Create initial black canvas
        self.image = Image.new('RGB', (self.width, self.height), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        if not test_mode:
            try:
                from displayhatmini import DisplayHATMini
                self.disp = DisplayHATMini(self.image)  # Pass the image as buffer
                # Rotate display 180 degrees
                self.disp.st7789._rotation = 2  # 0=0°, 1=90°, 2=180°, 3=270°
                
            except ImportError as e:
                print(f"Error importing displayhatmini: {e}")
                print("Running in test mode instead")
                self.test_mode = True
        
        # Try to load a font
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        except:
            self.font = ImageFont.load_default()

        # Network health indicators with PNG faces
        self.face_size = 100  # Size of the face in pixels
        self.network_states = {
            'excellent': 'assets/faces/excellent.png',
            'good': 'assets/faces/good.png',
            'fair': 'assets/faces/fair.png',
            'poor': 'assets/faces/poor.png',
            'critical': 'assets/faces/critical.png'
        }
        
        # Load and cache the face images
        self.face_images = {}
        for state, png_path in self.network_states.items():
            try:
                self.face_images[state] = Image.open(png_path).convert('RGBA')
            except Exception as e:
                print(f"Error loading face {png_path}: {e}")
                # Create a fallback image
                img = Image.new('RGBA', (self.face_size, self.face_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.text((self.face_size//2, self.face_size//2), "?", fill=(255, 255, 255, 255))
                self.face_images[state] = img

    def calculate_network_health(self, stats: NetworkStats) -> str:
        """Calculate network health based on ping, jitter, and packet loss"""
        score = 100
        
        # Ping scoring (0-40 points)
        if stats.ping < 20:
            score -= 0
        elif stats.ping < 50:
            score -= 10
        elif stats.ping < 100:
            score -= 20
        else:
            score -= 40
            
        # Jitter scoring (0-30 points)
        if stats.jitter < 5:
            score -= 0
        elif stats.jitter < 10:
            score -= 10
        elif stats.jitter < 20:
            score -= 20
        else:
            score -= 30
            
        # Packet loss scoring (0-30 points)
        if stats.packet_loss == 0:
            score -= 0
        elif stats.packet_loss < 1:
            score -= 10
        elif stats.packet_loss < 5:
            score -= 20
        else:
            score -= 30
            
        # Determine health state based on score
        if score >= 90:
            return 'excellent'
        elif score >= 70:
            return 'good'
        elif score >= 50:
            return 'fair'
        elif score >= 30:
            return 'poor'
        else:
            return 'critical'

    def update(self, stats: NetworkStats):
        """Update the display with network metrics"""
        # Clear the image
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        
        # Calculate network health and get corresponding symbol
        health_state = self.calculate_network_health(stats)
        symbol = self.network_states[health_state]
        
        # Make the face much larger
        large_font_size = 80
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", large_font_size)
        except:
            font_large = ImageFont.load_default()
        
        # Draw the network health symbol in the center
        text_bbox = self.draw.textbbox((0, 0), symbol, font=font_large)
        symbol_width = text_bbox[2] - text_bbox[0]
        symbol_height = text_bbox[3] - text_bbox[1]
        x = (self.width - symbol_width) // 2
        y = (self.height - symbol_height) // 2 - 20
        
        # Draw symbol with color based on health
        symbol_colors = {
            'excellent': (0, 255, 0),    # Green
            'good':     (144, 238, 144), # Light green
            'fair':     (255, 255, 0),   # Yellow
            'poor':     (255, 165, 0),   # Orange
            'critical': (255, 0, 0)      # Red
        }
        
        # Draw the face once but much larger
        self.draw.text((x, y), symbol, font=font_large, fill=symbol_colors[health_state])
        
        # Draw ping below the symbol
        ping_text = f"{stats.ping:.1f} ms"
        text_bbox = self.draw.textbbox((0, 0), ping_text, font=self.font)
        text_width = text_bbox[2] - text_bbox[0]
        x = (self.width - text_width) // 2
        self.draw.text((x, y + symbol_height + 20), ping_text, font=self.font, fill=(255, 255, 255))
        
        if self.test_mode:
            # Test mode console output
            print("\033c", end="")
            print("=== Network Monitor ===")
            print(f"Health: {health_state.upper()} {symbol}")
            print(f"Ping: {stats.ping:.1f} ms")
            print("-" * 30)
        else:
            # Update physical display
            self.disp.st7789.set_window()
            self.disp.st7789.display(self.image)

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
