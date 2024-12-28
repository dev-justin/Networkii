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
            score -= 20
        elif stats.packet_loss < 5:
            score -= 30
        else:
            score -= 40
            
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
        
        # Draw modern border - slightly inset from edges
        border_width = 2
        margin = 5
        self.draw.rectangle(
            (margin, margin, self.width - margin, self.height - margin),
            outline=(40, 40, 40),  # Dark gray
            width=border_width
        )
        
        # Draw separator line for stats
        line_x = 100  # Position of vertical line
        self.draw.line(
            (line_x, margin, line_x, self.height - margin),
            fill=(40, 40, 40),
            width=border_width
        )
        
        # Draw ping statistics on the left side
        stats_x = 15  # Left margin for text
        y_start = 30  # Starting Y position
        y_spacing = 35  # Space between lines
        
        # Current ping
        self.draw.text((stats_x, y_start), "PING", font=self.font, fill=(128, 128, 128))
        self.draw.text((stats_x, y_start + 20), f"{round(stats.ping)}", font=self.font, fill=(255, 255, 255))
        
        # Min ping
        self.draw.text((stats_x, y_start + y_spacing), "MIN", font=self.font, fill=(128, 128, 128))
        self.draw.text((stats_x, y_start + y_spacing + 20), f"{round(stats.min_ping)}", font=self.font, fill=(255, 255, 255))
        
        # Max ping
        self.draw.text((stats_x, y_start + y_spacing * 2), "MAX", font=self.font, fill=(128, 128, 128))
        self.draw.text((stats_x, y_start + y_spacing * 2 + 20), f"{round(stats.max_ping)}", font=self.font, fill=(255, 255, 255))
        
        # Avg ping
        self.draw.text((stats_x, y_start + y_spacing * 3), "AVG", font=self.font, fill=(128, 128, 128))
        self.draw.text((stats_x, y_start + y_spacing * 3 + 20), f"{round(stats.avg_ping)}", font=self.font, fill=(255, 255, 255))
        
        # Calculate network health and get corresponding face
        health_state = self.calculate_network_health(stats)
        face = self.face_images[health_state]
        
        # Calculate position to center the face in the right section
        face_x = line_x + (self.width - line_x - self.face_size) // 2
        face_y = (self.height - self.face_size) // 2
        
        # Draw the face
        self.image.paste(face, (face_x, face_y), face)
        
        if self.test_mode:
            # Test mode console output
            print("\033c", end="")
            print("=== Network Monitor ===")
            print(f"Health: {health_state.upper()}")
            print(f"Current: {round(stats.ping)} ms")
            print(f"Min/Max/Avg: {round(stats.min_ping)}/{round(stats.max_ping)}/{round(stats.avg_ping)} ms")
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
