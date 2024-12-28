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
    def __init__(self, test_mode: bool = False, network_monitor=None):
        self.test_mode = test_mode
        self.network_monitor = network_monitor  # Store reference to NetworkMonitor
        
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

    def calculate_bar_height(self, values: deque, max_value: float, bad_threshold: float) -> float:
        """Calculate health bar height based on historical values"""
        if not values:
            return 1.0
        # Calculate how many values are above the bad threshold
        bad_count = sum(1 for v in values if v > bad_threshold)
        # Return health percentage (1.0 = full health, 0.0 = no health)
        return 1.0 - (bad_count / len(values))

    def get_bar_color(self, health: float) -> tuple:
        """Get color for health bar based on health percentage"""
        if health > 0.8:
            return (0, 255, 0)  # Green
        elif health > 0.6:
            return (150, 255, 0)  # Yellow-green
        elif health > 0.4:
            return (255, 255, 0)  # Yellow
        elif health > 0.2:
            return (255, 165, 0)  # Orange
        else:
            return (255, 0, 0)  # Red

    def draw_health_bar(self, x: int, y: int, height: int, health: float, label: str):
        """Draw a vertical health bar"""
        bar_width = 15  # Increased from 10 to 15
        border_color = (40, 40, 40)
        label_padding = 15  # Space for label at bottom
        
        # Draw border (adjusted height to leave space for label)
        self.draw.rectangle(
            (x, y, x + bar_width, y + height - label_padding),
            outline=border_color,
            width=1
        )
        
        # Draw filled portion
        fill_height = int((height - label_padding) * health)
        if fill_height > 0:
            self.draw.rectangle(
                (x + 1, y + (height - label_padding) - fill_height, x + bar_width - 1, y + (height - label_padding) - 1),
                fill=self.get_bar_color(health)
            )
        
        # Draw label (moved up slightly from bottom)
        self.draw.text(
            (x + bar_width//2, y + height - 5),
            label,
            font=self.tiny_font,
            fill=(128, 128, 128),
            anchor="ms"  # middle-top anchor
        )

    def update(self, stats: NetworkStats):
        """Update the display with network metrics"""
        # Clear the image
        self.draw.rectangle((0, 0, self.width, self.height), fill=(0, 0, 0))
        
        # Load fonts with smaller sizes
        try:
            self.tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            self.number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            self.tiny_font = ImageFont.load_default()
            self.number_font = self.font

        # Calculate network health and get corresponding face
        health_state = self.calculate_network_health(stats)
        face = self.face_images[health_state]
        
        # Calculate positions
        face_x = (self.width - self.face_size) // 2
        face_y = (self.height - self.face_size) // 2
        
        # Draw health bars on the left with full height
        bar_height = self.height - 10  # Use almost full height, leave 5px padding top and bottom
        bar_y = 5  # Small padding from top
        
        # Calculate health percentages using NetworkMonitor's history
        ping_health = self.calculate_bar_height(
            self.network_monitor.ping_history, 100, 50)
        jitter_health = self.calculate_bar_height(
            self.network_monitor.jitter_history, 20, 10)
        loss_health = self.calculate_bar_height(
            self.network_monitor.packet_loss_history, 5, 1)
        
        # Draw the three bars with more spacing between them
        self.draw_health_bar(30, bar_y, bar_height, ping_health, "P")
        self.draw_health_bar(55, bar_y, bar_height, jitter_health, "J")
        self.draw_health_bar(80, bar_y, bar_height, loss_health, "L")
        
        # Helper function to draw metric
        def draw_metric(x, y, label, value, align='left'):
            self.draw.text((x, y), label, font=self.tiny_font, fill=(128, 128, 128))
            value_text = str(round(value))
            if align == 'left':
                self.draw.text((x, y + 12), value_text, font=self.number_font, fill=(0, 255, 0))
            else:  # right align
                text_bbox = self.draw.textbbox((0, 0), value_text, font=self.number_font)
                text_width = text_bbox[2] - text_bbox[0]
                self.draw.text((x - text_width, y + 12), value_text, font=self.number_font, fill=(0, 255, 0))

        # Draw current stats above face
        top_y = face_y - 60
        draw_metric(120, top_y, "PING", stats.ping)
        draw_metric(200, top_y, "JITTER", stats.jitter)
        draw_metric(280, top_y, "LOSS", stats.packet_loss)
        
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
    display = Display(test_mode=args.test, network_monitor=network_monitor)  # Pass NetworkMonitor instance

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
