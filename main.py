import time
import subprocess
import statistics
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from collections import deque
import netifaces
from displayhatmini import DisplayHATMini
import argparse

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

def get_preferred_interface():
    """Get the preferred network interface (usb0 with ICS standard IPv4 if available, otherwise wlan0)"""
    interfaces = netifaces.interfaces()
    
    if 'usb0' in interfaces:
        addrs = netifaces.ifaddresses('usb0')
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                if addr['addr'].startswith('192.168.137.'):
                    return 'usb0'
    
    return 'wlan0'

class NetworkMonitor:
    def __init__(self, target_host: str = "1.1.1.1", history_length: int = 300):
        self.target_host = target_host
        self.interface = get_preferred_interface()
        self.ping_history = deque(maxlen=history_length)
        self.jitter_history = deque(maxlen=history_length)
        self.packet_loss_history = deque(maxlen=history_length)

        print(f"Using interface: {self.interface}, target host: {self.target_host}")
    
    def get_stats(self, count=5, ping_interval=0.2) -> NetworkStats:
        """Execute ping command and return network statistics"""
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
    
    # Bar dimensions
    BAR_WIDTH = 8
    BAR_SPACING = 5
    BAR_START_X = 0
    
    # Face dimensions
    FACE_SIZE = 128
    
    # Heart dimensions
    HEART_SPACING = 10      # Vertical spacing between face and hearts
    HEART_GAP = 8          # Horizontal spacing between hearts
    HEART_SIZE = 28        # Size of each heart
    
    # Metric dimensions
    METRIC_WIDTH = 18    # Width of each metric column
    METRIC_SPACING = 5   # Space between columns
    METRIC_RIGHT_MARGIN = 0
    METRIC_TOP_MARGIN = 10
    METRIC_BOTTOM_MARGIN = 10
    
    # History settings
    RECENT_HISTORY_LENGTH = 20  # Number of samples to use for recent history

    # Font sizes
    FONT_LARGE = 16    # For current value
    FONT_MEDIUM = 14   # For past values
    FONT_SMALL = 10    # For labels
    FONT_MESSAGE = 14  # For network state message
    
    # Network states configuration
    NETWORK_STATES = {
        'excellent': {
            'message': "Network is Purring!",
            'face': 'assets/faces/excellent.png',
            'threshold': 90
        },
        'good': {
            'message': "All Systems Go!",
            'face': 'assets/faces/good.png',
            'threshold': 70
        },
        'fair': {
            'message': "Hanging in There!",
            'face': 'assets/faces/fair.png',
            'threshold': 60
        },
        'poor': {
            'message': "Having Hiccups... ",
            'face': 'assets/faces/poor.png',
            'threshold': 50
        },
        'critical': {
            'message': "Help, I'm Sick!",
            'face': 'assets/faces/critical.png',
            'threshold': 0
        }
    }

    def __init__(self, network_monitor=None):
        self.network_monitor = network_monitor
        
        # Create initial black canvas
        self.image = Image.new('RGB', (self.WIDTH, self.HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        # Initialize display
        self.disp = DisplayHATMini(self.image)
        
        # Load fonts
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            self.tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.FONT_SMALL)
            self.number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.FONT_LARGE)
            self.medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.FONT_MEDIUM)
            self.message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", self.FONT_MESSAGE)
        except:
            self.font = ImageFont.load_default()
            self.tiny_font = ImageFont.load_default()
            self.number_font = ImageFont.load_default()
            self.medium_font = ImageFont.load_default()
            self.message_font = ImageFont.load_default()

        # Load and cache the face images
        self.face_images = {}
        for state, info in self.NETWORK_STATES.items():
            try:
                image = Image.open(info['face']).convert('RGBA')
                self.face_images[state] = image.resize((self.FACE_SIZE, self.FACE_SIZE), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Error loading face {info['face']}: {e}")
                # Create a fallback image
                img = Image.new('RGBA', (self.FACE_SIZE, self.FACE_SIZE), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.text((self.FACE_SIZE//2, self.FACE_SIZE//2), "?", fill=(255, 255, 255, 255))
                self.face_images[state] = img

        # Load heart image
        try:
            self.heart_image = Image.open('assets/heart.png').convert('RGBA')
            self.heart_image = self.heart_image.resize((self.HEART_SIZE, self.HEART_SIZE))
        except Exception as e:
            print(f"Error loading heart image: {e}")
            # Create a fallback heart
            self.heart_image = Image.new('RGBA', (self.HEART_SIZE, self.HEART_SIZE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.heart_image)
            draw.text((self.HEART_SIZE//2, self.HEART_SIZE//2), "♥", fill=(255, 0, 0, 255))

    def calculate_network_health(self, stats: NetworkStats) -> tuple[int, str]:
        """Calculate network health based on recent history"""
        ping_history = list(stats.ping_history)[-self.RECENT_HISTORY_LENGTH:]
        jitter_history = list(stats.jitter_history)[-self.RECENT_HISTORY_LENGTH:]
        loss_history = list(stats.packet_loss_history)[-self.RECENT_HISTORY_LENGTH:]
        
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
        state = next((state for state, info in self.NETWORK_STATES.items() if final_score >= info['threshold']), 'critical')
        
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

    def draw_hearts(self, x: int, y: int, health_state: str):
        """Draw hearts based on network state"""
        total_hearts = 5
        filled_hearts = {
            'excellent': 5,
            'good': 4,
            'fair': 3,
            'poor': 2,
            'critical': 1
        }.get(health_state, 0)
        
        for i in range(total_hearts):
            heart_x = x + (i * (self.HEART_SIZE + self.HEART_GAP))
            if i < filled_hearts:
                self.image.paste(self.heart_image, (heart_x, y), self.heart_image)
            else:
                heart_outline = self.heart_image.copy()
                heart_outline.putalpha(50)
                self.image.paste(heart_outline, (heart_x, y), heart_outline)

    def show_home_screen(self, stats: NetworkStats):
        """Update the home screen with network metrics"""
        # Clear the image
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
        
        # Calculate width taken by health bars on the left
        health_bars_width = self.BAR_START_X + (self.BAR_WIDTH * 3) + (self.BAR_SPACING * 2)
        
        # Calculate width taken by metrics on the right
        metrics_width = (3 * (self.METRIC_WIDTH + self.METRIC_SPACING)) + self.METRIC_RIGHT_MARGIN
        
        # Calculate remaining width for face and hearts
        remaining_width = self.WIDTH - health_bars_width - metrics_width
        
        # Calculate face position (centered in remaining space)
        face_x = health_bars_width + (remaining_width - self.FACE_SIZE) // 2
        face_y = (self.HEIGHT - (self.FACE_SIZE + self.HEART_SIZE + self.HEART_SPACING)) // 2
        
        # Calculate metrics position (right-aligned)
        metrics_x = self.WIDTH - metrics_width
        
        # Draw metrics in full-height columns
        self.draw_metric(metrics_x, 0, "P", stats.ping_history, 'ping')
        self.draw_metric(metrics_x + self.METRIC_WIDTH + self.METRIC_SPACING, 0, "J", stats.jitter_history, 'jitter')
        self.draw_metric(metrics_x + (self.METRIC_WIDTH + self.METRIC_SPACING) * 2, 0, "L", stats.packet_loss_history, 'packet_loss')
        
        # Calculate total height of all elements
        message_bbox = self.draw.textbbox((0, 0), "Test", font=self.tiny_font)
        message_height = message_bbox[3] - message_bbox[1]
        total_element_height = (
            message_height +          # Message height
            20 +                      # Space between message and face
            self.FACE_SIZE +          # Face height
            self.HEART_SPACING +      # Space between face and hearts
            self.HEART_SIZE           # Hearts height
        )
        
        # Calculate starting Y position to center everything vertically
        start_y = (self.HEIGHT - total_element_height) // 2
        
        # Position each element
        message_y = start_y
        face_y = message_y + message_height + 20
        hearts_y = face_y + self.FACE_SIZE + self.HEART_SPACING
        
        # Draw network state message above face
        health_score, health_state = self.calculate_network_health(stats)
        message = self.NETWORK_STATES[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.message_font)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = face_x + (self.FACE_SIZE - message_width) // 2
        self.draw.text((message_x, message_y), message, font=self.message_font, fill=(255, 255, 255))
        
        # Draw the face
        self.image.paste(self.face_images[health_state], (face_x, face_y), self.face_images[health_state])
        
        # Draw hearts
        hearts_total_width = (5 * self.HEART_SIZE) + (4 * self.HEART_GAP)
        hearts_x = face_x + (self.FACE_SIZE - hearts_total_width) // 2
        self.draw_hearts(hearts_x, hearts_y, health_state)
        
        # Calculate health percentages using NetworkMonitor's history
        ping_health = self.calculate_bar_height(
            self.network_monitor.ping_history, 'ping')
        jitter_health = self.calculate_bar_height(
            self.network_monitor.jitter_history, 'jitter')
        loss_health = self.calculate_bar_height(
            self.network_monitor.packet_loss_history, 'packet_loss')
        
        # Draw the three bars with spacing
        self.draw_health_bar(self.BAR_START_X, 0, self.BAR_WIDTH, self.HEIGHT, ping_health, 'ping')
        self.draw_health_bar(self.BAR_START_X + self.BAR_WIDTH + self.BAR_SPACING, 0, self.BAR_WIDTH, self.HEIGHT, jitter_health, 'jitter')
        self.draw_health_bar(self.BAR_START_X + (self.BAR_WIDTH + self.BAR_SPACING) * 2, 0, self.BAR_WIDTH, self.HEIGHT, loss_health, 'packet_loss')

        # Remove test mode console output and just update display
        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def draw_metric(self, x: int, y: int, label: str, history: deque, metric_type: str):
        """Draw metric column with values using full height"""
        if not history:
            return
            
        color = self.get_outline_color(metric_type)
        
        # Draw label centered at top
        label_bbox = self.draw.textbbox((0, 0), label, font=self.tiny_font)
        label_width = label_bbox[2] - label_bbox[0]
        self.draw.text(
            (x + (self.METRIC_WIDTH - label_width) // 2, self.METRIC_TOP_MARGIN),
            label,
            font=self.tiny_font,
            fill=color
        )
        
        # Get last 10 values
        last_values = list(history)[-10:]
        if len(last_values) < 10:
            last_values = [0] * (10 - len(last_values)) + last_values
        
        # Calculate spacing for values
        available_height = self.HEIGHT - self.METRIC_TOP_MARGIN - self.METRIC_BOTTOM_MARGIN
        value_spacing = (available_height - 45) // 9  # Adjust for current value height
        
        # Draw most recent value larger
        current_value = str(round(last_values[-1]))
        current_bbox = self.draw.textbbox((0, 0), current_value, font=self.number_font)
        current_width = current_bbox[2] - current_bbox[0]
        self.draw.text(
            (x + (self.METRIC_WIDTH - current_width) // 2, self.METRIC_TOP_MARGIN + 20),
            current_value,
            font=self.number_font,
            fill=color
        )
        
        # Draw previous values from top to bottom with fading
        for i, value in enumerate(reversed(last_values[:-1]), 1):
            fade_level = 0.8 - (i * 0.08)
            faded_color = tuple(int(c * fade_level) for c in color)
            
            value_text = str(round(value))
            text_bbox = self.draw.textbbox((0, 0), value_text, font=self.medium_font)
            text_width = text_bbox[2] - text_bbox[0]
            
            text_x = x + (self.METRIC_WIDTH - text_width) // 2
            text_y = self.METRIC_TOP_MARGIN + 30 + (i * value_spacing)  # Adjusted spacing for larger font
            
            self.draw.text(
                (text_x, text_y),
                value_text,
                font=self.medium_font,
                fill=faded_color
            )

    def show_basic_screen(self, stats: NetworkStats):
        """Show the status screen with face and network state"""
        # Clear the image
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
        
        # Calculate network health and get state
        health_score, health_state = self.calculate_network_health(stats)
        
        # Define element heights and spacing
        SPACING = 20
        SCORE_HEIGHT = self.message_font.size  # Font size is the height
        MESSAGE_HEIGHT = self.message_font.size
        
        # Calculate total height and starting position
        total_height = SCORE_HEIGHT + SPACING + self.FACE_SIZE + SPACING + MESSAGE_HEIGHT
        start_y = (self.HEIGHT - total_height) // 2
        
        # Draw the score
        score_text = f"Health: {health_score}%"
        score_bbox = self.draw.textbbox((0, 0), score_text, font=self.message_font)
        score_width = score_bbox[2] - score_bbox[0]
        score_x = (self.WIDTH - score_width) // 2
        self.draw.text((score_x, start_y), score_text, font=self.message_font, fill=(255, 255, 255))
        
        # Draw the face centered
        face = self.face_images[health_state]
        face_x = (self.WIDTH - self.FACE_SIZE) // 2
        face_y = start_y + SCORE_HEIGHT + SPACING
        self.image.paste(face, (face_x, face_y), face)
        
        # Draw the status message
        message = self.NETWORK_STATES[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.message_font)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (self.WIDTH - message_width) // 2
        message_y = face_y + self.FACE_SIZE + SPACING
        self.draw.text((message_x, message_y), message, font=self.message_font, fill=(255, 255, 255))
        
        # Update display
        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def show_detailed_screen(self, stats: NetworkStats):
        """Show detailed network statistics with history"""
        # Clear the image
        self.draw.rectangle((0, 0, self.WIDTH, self.HEIGHT), fill=(0, 0, 0))
        
        # Define spacing and layout
        TOP_MARGIN = 15
        ROW_SPACING = 10  # Reduced spacing between rows
        LABEL_WIDTH = 80
        VALUE_WIDTH = self.WIDTH - LABEL_WIDTH - 20  # 20px right margin
        ROW_HEIGHT = 30  # Fixed height for each row instead of dividing screen
        
        # Helper function to draw a metric row
        def draw_metric_row(y: int, label: str, current_value: float, history: deque, color: tuple):
            # Draw label
            self.draw.text((10, y), label, font=self.message_font, fill=color)
            
            # Draw current value larger
            current_text = f"{round(current_value, 1)}"
            current_bbox = self.draw.textbbox((0, 0), current_text, font=self.number_font)
            current_width = current_bbox[2] - current_bbox[0]
            self.draw.text(
                (LABEL_WIDTH, y),
                current_text,
                font=self.number_font,
                fill=color
            )
            
            # Draw historical values with fade
            history_values = list(history)[-8:]  # Show last 8 values
            value_spacing = VALUE_WIDTH // 8
            
            for i, value in enumerate(reversed(history_values[:-1]), 1):
                fade_level = 0.7 - (i * 0.08)  # Start at 70% opacity
                faded_color = tuple(int(c * fade_level) for c in color)
                
                value_text = str(round(value, 1))
                self.draw.text(
                    (LABEL_WIDTH + (i * value_spacing), y + 5),  # Slight vertical offset
                    value_text,
                    font=self.tiny_font,
                    fill=faded_color
                )
        
        # Draw each metric
        draw_metric_row(
            TOP_MARGIN,  # First row starts at top margin
            "Ping:",
            stats.ping,
            stats.ping_history,
            self.get_outline_color('ping')
        )
        
        draw_metric_row(
            TOP_MARGIN + ROW_HEIGHT + ROW_SPACING,  # Second row
            "Jitter:",
            stats.jitter,
            stats.jitter_history,
            self.get_outline_color('jitter')
        )
        
        draw_metric_row(
            TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 2,  # Third row
            "Loss:",
            stats.packet_loss,
            stats.packet_loss_history,
            self.get_outline_color('packet_loss')
        )
        
        # Update display
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
        good=30,       # < 30ms is good
        fair=60,      # < 60ms is fair
        poor=100,      # < 100ms is poor, >= 100 is critical
        weight=0.4     # 40% of total score
    )
    
    JITTER = MetricThresholds(
        excellent=2,   # < 2ms is excellent
        good=5,        # < 5ms is good
        fair=10,       # < 10ms is fair
        poor=20,       # < 20ms is poor, >= 20 is critical
        weight=0.4     # 20% of total score
    )
    
    PACKET_LOSS = MetricThresholds(
        excellent=0,   # 0% is excellent
        good=0.1,      # < 0.1% is good
        fair=0.5,      # < 0.5% is fair
        poor=1,        # < 1% is poor, >= 1% is critical
        weight=0.2     # 40% of total score
    )
    
    @staticmethod
    def get_health_threshold(metric_type: str) -> float:
        """Get threshold for health bar calculation"""
        if metric_type == 'ping':
            return NetworkMetrics.PING.good
        elif metric_type == 'jitter':
            return NetworkMetrics.JITTER.fair
        else:  # packet loss
            return NetworkMetrics.PACKET_LOSS.excellent
    
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
    # Update argument parser
    parser = argparse.ArgumentParser(description='Network Monitor')
    parser.add_argument('--screen', type=int, choices=[1, 2, 3], default=1,
                       help='Screen to display (1=metrics, 2=status, 3=detailed)')
    args = parser.parse_args()

    print("\nNetwork Interfaces:")
    
    # Print all network interfaces
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        print(f"\nInterface: {interface}")
        
        # Print IPv4 addresses
        if netifaces.AF_INET in addrs:
            for addr in addrs[netifaces.AF_INET]:
                print(f"  IPv4: {addr['addr']}")
                if 'netmask' in addr:
                    print(f"  Netmask: {addr['netmask']}")
                if 'broadcast' in addr:
                    print(f"  Broadcast: {addr['broadcast']}")

    network_monitor = NetworkMonitor()
    display = Display(network_monitor=network_monitor)

    try:
        while True:
            stats = network_monitor.get_stats()
            if args.screen == 1:
                display.show_home_screen(stats)
            elif args.screen == 2:
                display.show_basic_screen(stats)
            else:
                display.show_detailed_screen(stats)
            time.sleep(2)
    except KeyboardInterrupt:
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
