import time
import subprocess
import statistics
import argparse
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from collections import deque

@dataclass 
class NetworkStats:
    timestamp: float
    ping_history: deque
    jitter_history: deque
    packet_loss_history: deque
    
    @property
    def ping(self) -> float:
        """Current ping"""
        return self.ping_history[-1] if self.ping_history else 0
        
    @property
    def jitter(self) -> float:
        """Current jitter"""
        return self.jitter_history[-1] if self.jitter_history else 0
        
    @property
    def packet_loss(self) -> float:
        """Current packet loss"""
        return self.packet_loss_history[-1] if self.packet_loss_history else 0

class NetworkMonitor:
    def __init__(self, target_host: str = "1.1.1.1", history_length: int = 600):
        self.target_host = target_host
        self.ping_history = deque(maxlen=history_length)
        self.jitter_history = deque(maxlen=history_length)
        self.packet_loss_history = deque(maxlen=history_length)
        
    def get_stats(self, count=3, ping_interval=0.25) -> NetworkStats:
        """Execute ping command and return network statistics"""
        try:
            cmd = ['ping', '-c', str(count), '-i', str(ping_interval), self.target_host]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            times = []
            packets_received = 0
            
            for line in result.stdout.splitlines():
                if 'time=' in line:
                    time_str = line.split('time=')[1].split()[0]
                    times.append(float(time_str))
                    packets_received += 1
            
            # Calculate values
            avg_ping = statistics.mean(times) if times else 0
            jitter = statistics.stdev(times) if len(times) > 1 else 0
            packet_loss = ((count - packets_received) / count) * 100
            
            # Update histories
            if avg_ping > 0:
                self.ping_history.append(avg_ping)
            if jitter >= 0:
                self.jitter_history.append(jitter)
            self.packet_loss_history.append(packet_loss)
            
            return NetworkStats(
                timestamp=time.time(),
                ping_history=self.ping_history,
                jitter_history=self.jitter_history,
                packet_loss_history=self.packet_loss_history
            )
            
        except Exception as e:
            print(f"Error during ping: {e}")
            return NetworkStats(
                timestamp=time.time(),
                ping_history=self.ping_history,
                jitter_history=self.jitter_history,
                packet_loss_history=self.packet_loss_history
            )

class Display:

    # Display dimensions
    WIDTH = 320 
    HEIGHT = 240

    def __init__(self, test_mode: bool = False, network_monitor=None):
        self.test_mode = test_mode
        self.network_monitor = network_monitor
        
        # Create initial black canvas
        self.image = Image.new('RGB', (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        if not test_mode:
            try:
                from displayhatmini import DisplayHATMini
                self.disp = DisplayHATMini(self.image)
                self.disp.st7789._rotation = 2
                
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
        self.face_size = 92  # Size of the face in pixels
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
                image = Image.open(png_path).convert('RGBA')
                self.face_images[state] = image.resize((self.face_size, self.face_size), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Error loading face {png_path}: {e}")
                # Create a fallback image
                img = Image.new('RGBA', (self.face_size, self.face_size), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.text((self.face_size//2, self.face_size//2), "?", fill=(255, 255, 255, 255))
                self.face_images[state] = img

        # Load heart image
        try:
            self.heart_image = Image.open('assets/heart.png').convert('RGBA')
            self.heart_size = 26  # Size to display hearts
            self.heart_image = self.heart_image.resize((self.heart_size, self.heart_size))
        except Exception as e:
            print(f"Error loading heart image: {e}")
            # Create a fallback heart
            self.heart_image = Image.new('RGBA', (self.heart_size, self.heart_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.heart_image)
            draw.text((self.heart_size//2, self.heart_size//2), "♥", fill=(255, 0, 0, 255))

    def calculate_network_health(self, stats: NetworkStats, history_length: int = 15) -> tuple[int, str]:
        """Calculate network health based on recent history (last ~15 seconds)"""
        # Get last 15 items from history
        ping_history = list(self.network_monitor.ping_history)[-history_length:]
        jitter_history = list(self.network_monitor.jitter_history)[-history_length:]
        loss_history = list(self.network_monitor.packet_loss_history)[-history_length:]
        
        current_score = 100
        
        # Calculate penalties with higher weights for recent issues
        if ping_history:
            bad_pings = sum(1 for p in ping_history if p > 100)
            ping_penalty = (bad_pings / len(ping_history)) * 40
            current_score -= ping_penalty
        
        if jitter_history:
            bad_jitter = sum(1 for j in jitter_history if j > 20)
            jitter_penalty = (bad_jitter / len(jitter_history)) * 30
            current_score -= jitter_penalty
            
        if loss_history:
            bad_loss = sum(1 for l in loss_history if l > 0)  # More sensitive to any packet loss
            loss_penalty = (bad_loss / len(loss_history)) * 30
            current_score -= loss_penalty
        
        # Add current state impact (30% current, 70% history)
        current_impact = 0.3
        history_impact = 0.7
        
        # Calculate current state penalty
        current_penalty = 0
        if stats.ping > 100: current_penalty += 40
        if stats.jitter > 20: current_penalty += 30
        if stats.packet_loss > 0: current_penalty += 30
        
        # Blend current and historical scores
        final_score = (current_score * history_impact) + ((100 - current_penalty) * current_impact)
        final_score = max(0, min(100, final_score))
        
        state = 'excellent' if final_score >= 90 else \
                'good' if final_score >= 70 else \
                'fair' if final_score >= 50 else \
                'poor' if final_score >= 30 else \
                'critical'
        
        return int(final_score), state

    def calculate_bar_height(self, values: deque, bad_threshold: float) -> float:
        """Calculate health bar height based on historical values"""
        if not values:
            return 1.0
        # Calculate how many values are above the bad threshold
        bad_count = sum(1 for v in values if v > bad_threshold)
        # Return health percentage (1.0 = full health, 0.0 = no health)
        return 1.0 - (bad_count / len(values))

    def get_outline_color(self, metric_type: str) -> tuple:
        """Get color for bar outline based on metric type"""
        if metric_type == 'ping':
            return (64, 224, 208)  # Turquoise
        elif metric_type == 'jitter':
            return (95, 158, 160)  # Cadet Blue
        else:  # packet loss
            return (176, 196, 222)  # Light Steel Blue

    def draw_health_bar(self, x: int, y: int, width: int, height: int, health: float, metric_type: str):
        """Draw a segmented health bar in retro style"""
        color = self.get_outline_color(metric_type)
        
        # Calculate segments
        total_segments = 10
        segment_spacing = 2
        # Calculate segment height accounting for spacing
        total_spacing = segment_spacing * (total_segments - 1)
        segment_height = (height - total_spacing) // total_segments
        filled_segments = round(health * total_segments)
        
        # Draw segments from bottom to top
        for i in range(total_segments):
            # Calculate y position accounting for spacing
            segment_y = y + height - ((i + 1) * segment_height + i * segment_spacing)
            
            # Determine if segment should be filled
            if i < filled_segments:
                # Draw filled segment
                self.draw.rectangle(
                    (x, segment_y, x + width, segment_y + segment_height),
                    fill=color
                )
            else:
                # Draw empty segment outline
                self.draw.rectangle(
                    (x, segment_y, x + width, segment_y + segment_height),
                    outline=color,
                    width=1
                )

    def draw_hearts(self, x: int, y: int, health_score: int):
        """Draw hearts based on health score (0-100)"""
        total_hearts = 5
        filled_hearts = round((health_score / 100.0) * total_hearts)
        
        for i in range(total_hearts):
            heart_x = x + (i * (self.heart_size + 5))  # 5px spacing between hearts
            if i < filled_hearts:
                # Draw filled heart
                self.image.paste(self.heart_image, (heart_x, y), self.heart_image)
            else:
                # Draw empty heart (could be a different image or just outline) || TODO: Add half heart image
                heart_outline = self.heart_image.copy()
                # Make it semi-transparent for empty state
                heart_outline.putalpha(50)
                self.image.paste(heart_outline, (heart_x, y), heart_outline)

    def update(self, stats: NetworkStats):
        """Update the display with network metrics"""
        # Clear the image
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
        
        # Load fonts with smaller sizes
        try:
            self.tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            self.number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        except:
            self.tiny_font = ImageFont.load_default()
            self.number_font = self.font

        # Calculate network health and get corresponding face
        health_score, health_state = self.calculate_network_health(stats)
        face = self.face_images[health_state]
        
        # Calculate positions for face and hearts
        face_x = (self.WIDTH - self.face_size) // 2
        face_y = (self.HEIGHT - (self.face_size + self.heart_size + 30)) // 2
        
        # Draw health bars on the left with full height and spacing
        bar_height = self.HEIGHT  # Use full height
        bar_y = 0  # Start from top
        bar_width = 12  # Wider bars
        bar_spacing = 6  # Slightly more spacing for wider bars
        
        # Calculate total width of bars including spacing
        start_x = 15  # Slightly more left margin
        
        # Calculate health percentages using NetworkMonitor's history
        ping_health = self.calculate_bar_height(
            self.network_monitor.ping_history, 50)
        jitter_health = self.calculate_bar_height(
            self.network_monitor.jitter_history, 10)
        loss_health = self.calculate_bar_height(
            self.network_monitor.packet_loss_history, 1)
        
        # Draw the three bars with spacing
        self.draw_health_bar(start_x, bar_y, bar_width, bar_height, ping_health, 'ping')
        self.draw_health_bar(start_x + bar_width + bar_spacing, bar_y, bar_width, bar_height, jitter_health, 'jitter')
        self.draw_health_bar(start_x + (bar_width + bar_spacing) * 2, bar_y, bar_width, bar_height, loss_health, 'packet_loss')
        
        # Helper function to draw metric with matching color and right alignment
        def draw_metric(y, label, value, metric_type):
            color = self.get_outline_color(metric_type)
            # Draw label
            self.draw.text((self.WIDTH - 20, y), label, font=self.tiny_font, fill=color, anchor="rt")
            # Draw value right-aligned
            value_text = str(round(value))
            self.draw.text((self.WIDTH - 20, y + 12), value_text, font=self.number_font, fill=color, anchor="rt")

        # Draw current stats on right side, evenly spaced vertically
        total_metrics = 3
        spacing = self.HEIGHT // (total_metrics + 2)  # Divide height into 5 parts for 3 metrics + top/bottom spacing
        
        # Draw metrics evenly spaced (starting at 1/5, ending at 4/5)
        draw_metric(spacing, "PING", stats.ping, 'ping')
        draw_metric(spacing * 2, "JITTER", stats.jitter, 'jitter')
        draw_metric(spacing * 3, "LOSS", stats.packet_loss, 'packet_loss')
        
        # Draw the face
        self.image.paste(face, (face_x, face_y), face)
        
        # Calculate and draw hearts below face with proper spacing
        hearts_total_width = (5 * self.heart_size) + (4 * 7)  # 5 hearts with 5px spacing
        hearts_x = (self.WIDTH - hearts_total_width) // 2
        hearts_y = face_y + self.face_size + 30  # 15px spacing between face and hearts
        self.draw_hearts(hearts_x, hearts_y, health_score)
        
        if self.test_mode:
            # Test mode console output
            print("\033c", end="")
            print("=== Network Monitor ===")
            print(f"Health: {health_state.upper()}")
            print(f"Current: {round(stats.ping)} ms")
            print(f"Avg: {round(statistics.mean(stats.ping_history))} ms")
            print("-" * 30)
        else:
            # Update physical display
            self.disp.st7789.set_window()
            self.disp.st7789.display(self.image)

def main():
    parser = argparse.ArgumentParser(description='Network Monitor')
    parser.add_argument('--test', action='store_true', help='Run in test mode (no physical display)')
    args = parser.parse_args()

    network_monitor = NetworkMonitor()
    display = Display(test_mode=args.test, network_monitor=network_monitor)  # Pass NetworkMonitor instance

    try:
        while True:
            stats = network_monitor.get_stats()
            display.update(stats)
            time.sleep(1) # Sleep for 1 second
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
