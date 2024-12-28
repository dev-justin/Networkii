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
        self.face_size = 128  # Size of the face in pixels
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
            self.heart_size = 30  # Size to display hearts
            self.heart_image = self.heart_image.resize((self.heart_size, self.heart_size))
        except Exception as e:
            print(f"Error loading heart image: {e}")
            # Create a fallback heart
            self.heart_image = Image.new('RGBA', (self.heart_size, self.heart_size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.heart_image)
            draw.text((self.heart_size//2, self.heart_size//2), "♥", fill=(255, 0, 0, 255))

    def calculate_network_health(self, stats: NetworkStats, history_length: int = 30) -> tuple[int, str]:
        """Calculate network health based on recent history"""
        ping_history = list(stats.ping_history)[-history_length:]
        jitter_history = list(stats.jitter_history)[-history_length:]
        loss_history = list(stats.packet_loss_history)[-history_length:]
        
        # Calculate historical scores
        if ping_history:
            ping_scores = [NetworkMetrics.calculate_metric_score(p, NetworkMetrics.PING) for p in ping_history]
            ping_score = statistics.mean(ping_scores) * NetworkMetrics.PING.weight
        
        if jitter_history:
            jitter_scores = [NetworkMetrics.calculate_metric_score(j, NetworkMetrics.JITTER) for j in jitter_history]
            jitter_score = statistics.mean(jitter_scores) * NetworkMetrics.JITTER.weight
            
        if loss_history:
            loss_scores = [NetworkMetrics.calculate_metric_score(l, NetworkMetrics.PACKET_LOSS) for l in loss_history]
            loss_score = statistics.mean(loss_scores) * NetworkMetrics.PACKET_LOSS.weight
        
        # Calculate final score
        final_score = ping_score + jitter_score + loss_score
        final_score = max(0, min(100, final_score))
        
        # Determine state based on score
        state = 'excellent' if final_score >= 90 else \
                'good' if final_score >= 70 else \
                'fair' if final_score >= 50 else \
                'poor' if final_score >= 30 else \
                'critical'
        
        return int(final_score), state

    def calculate_bar_height(self, values: deque, metric_type: str) -> float:
        """Calculate health bar height based on historical values"""
        if not values:
            return 1.0
        threshold = NetworkMetrics.get_health_threshold(metric_type)
        bad_count = sum(1 for v in values if v > threshold)
        return 1.0 - (bad_count / len(values))

    def get_outline_color(self, metric_type: str) -> tuple:
        """Get color for bar outline based on metric type"""
        if metric_type == 'ping':
            return (0, 255, 127)  # Spring Green
        elif metric_type == 'jitter':
            return (255, 99, 71)  # Tomato Red
        else:  # packet loss
            return (147, 112, 219)  # Medium Purple

    def draw_health_bar(self, x: int, y: int, width: int, height: int, health: float, metric_type: str):
        """Draw a retro-style health bar"""
        color = self.get_outline_color(metric_type)
        dim_color = tuple(max(0, c // 3) for c in color)  # Dimmed version of color
        
        # Draw outer border (3px thick)
        border_color = (80, 80, 80)  # Dark gray border
        self.draw.rectangle(
            (x - 2, y - 2, x + width + 2, y + height + 2),
            outline=border_color,
            width=1
        )
        
        # Calculate segments
        total_segments = 20  # More segments for smoother look
        segment_height = height // total_segments
        filled_segments = round(health * total_segments)
        
        # Draw background grid (empty segments)
        for i in range(total_segments):
            segment_y = y + height - ((i + 1) * segment_height)
            # Draw dim background segments
            self.draw.rectangle(
                (x, segment_y, x + width, segment_y + segment_height - 1),
                fill=dim_color
            )
            # Draw segment separator lines
            self.draw.line(
                (x, segment_y, x + width, segment_y),
                fill=(0, 0, 0),
                width=1
            )
        
        # Draw filled segments from bottom up
        if filled_segments > 0:
            fill_height = filled_segments * segment_height
            self.draw.rectangle(
                (x, y + height - fill_height, x + width, y + height),
                fill=color
            )
            
            # Draw segment lines over filled area
            for i in range(filled_segments):
                line_y = y + height - ((i + 1) * segment_height)
                self.draw.line(
                    (x, line_y, x + width, line_y),
                    fill=(0, 0, 0),
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
        
        # Calculate width taken by health bars on the left
        bar_width = 12
        bar_spacing = 6
        start_x = 15
        bars_total_width = start_x + (bar_width * 3) + (bar_spacing * 2) + 20  # Add right margin
        
        # Calculate remaining width for center content
        remaining_width = self.WIDTH - bars_total_width
        
        # Define spacing constants
        HEART_SPACING = 10
        METRIC_SPACING = 60
        
        # Calculate total height of all elements (metrics + face + hearts)
        metrics_height = 40
        total_element_height = metrics_height + self.face_size + self.heart_size + HEART_SPACING
        
        # Calculate starting Y position to center everything vertically
        start_y = (self.HEIGHT - total_element_height) // 2
        
        # Calculate metrics positioning in remaining space
        metrics_total_width = (3 * 40) + (2 * METRIC_SPACING) + 20
        metrics_start_x = bars_total_width + (remaining_width - metrics_total_width) // 2
        
        # Helper function to draw metric with matching color and horizontal alignment
        def draw_metric(x, y, label, value, metric_type):
            color = self.get_outline_color(metric_type)
            # Draw label centered above value
            label_bbox = self.draw.textbbox((0, 0), label, font=self.tiny_font)
            label_width = label_bbox[2] - label_bbox[0]
            self.draw.text((x + (40 - label_width) // 2, y), label, font=self.tiny_font, fill=color)
            # Draw value centered below label
            value_text = str(round(value))
            value_bbox = self.draw.textbbox((0, 0), value_text, font=self.number_font)
            value_width = value_bbox[2] - value_bbox[0]
            self.draw.text((x + (40 - value_width) // 2, y + 12), value_text, font=self.number_font, fill=color)

        # Draw metrics horizontally above face
        draw_metric(metrics_start_x, start_y, "PING", stats.ping, 'ping')
        draw_metric(metrics_start_x + 40 + METRIC_SPACING, start_y, "JITTER", stats.jitter, 'jitter')
        draw_metric(metrics_start_x + (40 + METRIC_SPACING) * 2, start_y, "LOSS", stats.packet_loss, 'packet_loss')
        
        # Set positions for face centered in remaining space
        face_x = bars_total_width + (remaining_width - self.face_size) // 2
        face_y = start_y + metrics_height
        
        # Draw the face
        self.image.paste(face, (face_x, face_y), face)
        
        # Calculate and draw hearts below face
        heart_spacing = 7
        hearts_total_width = (5 * self.heart_size) + (4 * heart_spacing)
        face_center_x = face_x + (self.face_size // 2)
        hearts_x = face_center_x - (hearts_total_width // 2)
        hearts_y = face_y + self.face_size + HEART_SPACING
        self.draw_hearts(hearts_x, hearts_y, health_score)
        
        # Draw health bars on the left with full height and spacing
        bar_height = self.HEIGHT  # Use full height
        bar_y = 0  # Start from top
        bar_width = 12  # Wider bars
        bar_spacing = 6  # Slightly more spacing for wider bars
        start_x = 15  # Left margin
        
        # Calculate health percentages using NetworkMonitor's history
        ping_health = self.calculate_bar_height(
            self.network_monitor.ping_history, 'ping')
        jitter_health = self.calculate_bar_height(
            self.network_monitor.jitter_history, 'jitter')
        loss_health = self.calculate_bar_height(
            self.network_monitor.packet_loss_history, 'packet_loss')
        
        # Draw the three bars with spacing
        self.draw_health_bar(start_x, bar_y, bar_width, bar_height, ping_health, 'ping')
        self.draw_health_bar(start_x + bar_width + bar_spacing, bar_y, bar_width, bar_height, jitter_health, 'jitter')
        self.draw_health_bar(start_x + (bar_width + bar_spacing) * 2, bar_y, bar_width, bar_height, loss_health, 'packet_loss')

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

@dataclass
class MetricThresholds:
    """Thresholds for network metrics"""
    excellent: float
    good: float
    fair: float
    poor: float
    weight: float  # How much this metric affects overall score (0-1)

class NetworkMetrics:
    """Centralized network metrics configuration"""
    
    # Define thresholds for each metric
    PING = MetricThresholds(
        excellent=20,  # < 20ms is excellent
        good=40,       # < 40ms is good
        fair=80,      # < 80ms is fair
        poor=120,      # < 120ms is poor, >= 120 is critical
        weight=0.4     # 40% of total score
    )
    
    JITTER = MetricThresholds(
        excellent=2,   # < 2ms is excellent
        good=5,        # < 5ms is good
        fair=10,       # < 10ms is fair
        poor=20,       # < 20ms is poor, >= 20 is critical
        weight=0.2     # 20% of total score
    )
    
    PACKET_LOSS = MetricThresholds(
        excellent=0,   # 0% is excellent
        good=0.1,      # < 0.1% is good
        fair=0.5,      # < 0.5% is fair
        poor=1,        # < 1% is poor, >= 1% is critical
        weight=0.4     # 40% of total score
    )
    
    @staticmethod
    def get_health_threshold(metric_type: str) -> float:
        """Get threshold for health bar calculation"""
        if metric_type == 'ping':
            return NetworkMetrics.PING.good
        elif metric_type == 'jitter':
            return NetworkMetrics.JITTER.good
        else:  # packet loss
            return NetworkMetrics.PACKET_LOSS.good
    
    @staticmethod
    def calculate_metric_score(value: float, thresholds: MetricThresholds) -> float:
        """Calculate score (0-100) for a metric based on its thresholds"""
        if value <= thresholds.excellent:
            return 100
        elif value <= thresholds.good:
            return 75
        elif value <= thresholds.fair:
            return 50
        elif value <= thresholds.poor:
            return 25
        else:
            return 0

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
