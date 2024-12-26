import time
import speedtest
from ping3 import ping
from PIL import Image, ImageDraw, ImageFont
import threading
import argparse
import config
from collections import deque
from config import get  # Add this import

# Try to import ST7789, but don't fail if not available
try:
    import ST7789
    ST7789_AVAILABLE = True
except ImportError:
    ST7789_AVAILABLE = False

# Add argument parser for test mode
parser = argparse.ArgumentParser()
parser.add_argument('--test', action='store_true', help='Run in test mode with console output')
args = parser.parse_args()

# Force test mode if ST7789 is not available
if not ST7789_AVAILABLE and not args.test:
    print("Warning: ST7789 library not available. Forcing test mode.")
    args.test = True

class DisplayOutput:
    def reinit_display(self):
        """Reinitialize the display with new settings"""
        if not self.test_mode:
            self.disp = ST7789.ST7789(
                height=get('display_height'),
                width=get('display_width'),
                rotation=get('display_rotation'),
                port=0,
                cs=1,
                dc=9,
                backlight=13,
                spi_speed_hz=60 * 1000 * 1000,
                offset_left=0,
                offset_top=0
            )
            self.disp.begin()

    def __init__(self, test_mode=False):
        self.test_mode = test_mode
        self.last_print_time = 0
        if not test_mode:
            self.reinit_display()
            # Register callbacks for display settings
            config.config.register_callback('display_width', lambda x: self.reinit_display())
            config.config.register_callback('display_height', lambda x: self.reinit_display())
            config.config.register_callback('display_rotation', lambda x: self.reinit_display())

    def display(self, image, stats):
        if self.test_mode:
            current_time = time.time()
            if current_time - self.last_print_time >= get('display_refresh'):
                print("\033[2J\033[H")  # Clear screen and move cursor to top
                print("=== Network Monitor ===")
                print(f"Download: {stats['download']:.1f} Mbps")
                print(f"Upload: {stats['upload']:.1f} Mbps")
                print(f"Ping: {stats['ping']:.0f} ms")
                print(f"Packet Loss: {stats['packet_loss']:.1f}%")
                print("=====================")
                self.last_print_time = current_time
        else:
            self.disp.display(image)

# Initialize display based on mode
display_output = DisplayOutput(test_mode=args.test)

# Global variables to store network metrics
network_stats = {
    'download': 0,
    'upload': 0,
    'ping': 0,
    'packet_loss': 0,
    'jitter': 0,
    'connection_quality': 'Unknown',
    'external_ip': 'Checking...'
}

# Add ping history storage
def reinit_ping_history(new_size):
    """Reinitialize ping history with new size"""
    global ping_history
    try:
        print(f"Reinitializing ping history with size {new_size}")  # Debug
        old_data = list(ping_history)
        ping_history = deque(maxlen=new_size)
        # Preserve as much old data as possible
        for item in old_data[-new_size:]:
            ping_history.append(item)
        print("Ping history reinitialized successfully")  # Debug
    except Exception as e:
        print(f"Error reinitializing ping history: {e}")

# Register callbacks for initialization-dependent values
config.config.register_callback('graph_duration', reinit_ping_history)

# Initialize with current values
ping_history = deque(maxlen=get('graph_duration'))

def reinit_ping_deque(new_size):
    """Reinitialize ping tracking deque"""
    global last_pings
    try:
        print(f"Reinitializing ping deque with size {new_size}")  # Debug
        if 'last_pings' in globals():  # Check if last_pings exists
            old_data = list(last_pings)
            last_pings = deque(maxlen=new_size)
            # Preserve as much old data as possible
            for item in old_data[-new_size:]:
                last_pings.append(item)
        else:
            last_pings = deque(maxlen=new_size)
        print("Ping deque reinitialized successfully")  # Debug
    except Exception as e:
        print(f"Error reinitializing ping deque: {e}")

# Register callbacks for initialization-dependent values
config.config.register_callback('ping_count', reinit_ping_deque)

def run_speed_test():
    """Run speed test and update global network_stats"""
    while True:
        try:
            interval = get('speedtest_interval')  # Get current interval each time
            print("Starting speed test...")
            st = speedtest.Speedtest()
            network_stats['download'] = st.download() / 1_000_000
            network_stats['upload'] = st.upload() / 1_000_000
            print("Speed test completed")
        except Exception as e:
            print(f"Speed test error: {e}")
        time.sleep(interval)  # Use current interval

def draw_ping_graph(draw, font):
    """Draw the ping graph with grid lines"""
    # Draw graph border
    draw.rectangle(
        [10, 170,  # Using fixed values for GRAPH_X and GRAPH_Y 
         10 + 300, # Using fixed width
         170 + 60], # Using fixed height
        outline=config.GRAPH_GRID_COLOR
    )
    
    # Draw horizontal grid lines
    for i in range(1, 4):  # Draw 3 horizontal lines
        y = 170 + (i * (60 / 4))  # Using fixed height
        draw.line(
            [10, y, 10 + 300, y],  # Using fixed width
            fill=config.GRAPH_GRID_COLOR
        )
        # Draw ping values on grid lines
        ping_value = get('graph_max_ping') - (i * (get('graph_max_ping') / 4))
        draw.text(
            (10 - 8, y - 6),
            f"{int(ping_value)}",
            font=font,
            fill=config.GRAPH_GRID_COLOR,
            anchor="rm"
        )
    
    # Draw the ping history line
    if len(ping_history) > 1:
        points = []
        for i, ping_value in enumerate(ping_history):
            x = 10 + (i * (300 / get('graph_duration')))
            # Scale ping value to graph height
            scaled_ping = max(min(ping_value, get('graph_max_ping')), 0)
            y = 170 + 60 - (
                (scaled_ping - 0) * 
                60 / (get('graph_max_ping') - 0)
            )
            points.append((x, y))
        
        # Draw lines connecting the points
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=config.GRAPH_COLOR)

def calculate_connection_quality(ping, jitter, packet_loss):
    """Calculate connection quality based on ping, jitter, and packet loss"""
    # Start with maximum score of 100
    score = 100
    
    # Ping scoring
    if ping <= get('ping_excellent'):
        score -= 0
    elif ping <= get('ping_good'):
        score -= 10
    elif ping <= get('ping_fair'):
        score -= 20
    else:
        score -= 30

    # Jitter scoring
    if jitter <= get('jitter_excellent'):
        score -= 0
    elif jitter <= get('jitter_good'):
        score -= 10
    elif jitter <= get('jitter_fair'):
        score -= 20
    else:
        score -= 30

    # Packet loss scoring
    if packet_loss <= get('loss_excellent'):
        score -= 0
    elif packet_loss <= get('loss_good'):
        score -= 10
    elif packet_loss <= get('loss_fair'):
        score -= 20
    else:
        score -= 30

    # Determine quality label and color
    if score >= 90:     
        return 'Excellent', config.COLOR_EXCELLENT
    elif score >= 75:
        return 'Good', config.COLOR_GOOD
    elif score >= 60:
        return 'Fair', config.COLOR_FAIR
    else:
        return 'Poor', config.COLOR_POOR

def check_ping_and_packet_loss():
    """Check ping and packet loss to configured target"""
    while True:
        try:
            ping_times = []
            lost_packets = 0
            current_count = get('ping_count')  # Get current count each time
            
            for _ in range(current_count):
                result = ping(get('ping_target'), timeout=get('ping_timeout'))
                if result is None:
                    lost_packets += 1
                else:
                    ping_time = result * 1000
                    ping_times.append(ping_time)
                    if 'last_pings' in globals():  # Check if last_pings exists
                        last_pings.append(ping_time)
                time.sleep(0.1)
            
            if ping_times:  # Only update if we have valid pings
                avg_ping = sum(ping_times) / len(ping_times)
                packet_loss = (lost_packets / current_count) * 100
                
                network_stats['ping'] = avg_ping
                network_stats['packet_loss'] = packet_loss
                
                if len(ping_times) >= 2:
                    differences = [abs(ping_times[i] - ping_times[i-1]) for i in range(1, len(ping_times))]
                    network_stats['jitter'] = sum(differences) / len(differences)
                
                quality, _ = calculate_connection_quality(avg_ping, network_stats['jitter'], packet_loss)
                network_stats['connection_quality'] = quality
                
                ping_history.append(avg_ping)
            
        except Exception as e:
            print(f"Ping test error: {e}")
        
        time.sleep(get('ping_interval'))

def check_external_ip():
    """Check external IP address periodically using speedtest"""
    while True:
        try:
            st = speedtest.Speedtest()
            config = st.get_config()
            network_stats['external_ip'] = config['client']['ip']
        except Exception as e:
            print(f"External IP check error: {e}")
            network_stats['external_ip'] = 'Error'
        time.sleep(300)  # Check every 5 minutes

def get_quality_face(quality):
    """Return ASCII face based on connection quality"""
    faces = {
        'Excellent': config.FACE_EXCELLENT,
        'Good': config.FACE_GOOD,
        'Fair': config.FACE_FAIR,
        'Poor': config.FACE_POOR
    }
    return faces.get(quality, '(?_?)')  # Default confused face if quality unknown

def update_display():
    """Update the display with current network statistics"""
    if not args.test:
        # Load fonts only if using the actual display
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", config.TITLE_FONT_SIZE)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", config.TEXT_FONT_SIZE)

    while True:
        if not args.test:
            # Create a new image with a black background
            image = Image.new('RGB', (get('display_width'), get('display_height')), color=config.COLOR_BACKGROUND)
            draw = ImageDraw.Draw(image)

            # Get quality color and face for display
            _, quality_color = calculate_connection_quality(
                network_stats['ping'],
                network_stats['jitter'],
                network_stats['packet_loss']
            )
            quality_face = get_quality_face(network_stats['connection_quality'])

            # Draw network statistics
            draw.text((10, 10), "Network Monitor", font=font, fill=config.COLOR_TITLE)
            # Draw quality face with quality color
            draw.text((280, 10), quality_face, font=font, fill=quality_color)
            
            draw.text((10, 40), f"Download: {network_stats['download']:.1f} Mbps", font=small_font, fill=config.COLOR_SPEED)
            draw.text((10, 70), f"Upload: {network_stats['upload']:.1f} Mbps", font=small_font, fill=config.COLOR_SPEED)
            draw.text((10, 100), f"Ping: {network_stats['ping']:.0f} ms", font=small_font, fill=config.COLOR_PING)
            draw.text((10, 130), f"Jitter: {network_stats['jitter']:.1f} ms", font=small_font, fill=config.COLOR_PING)
            draw.text((160, 130), f"Quality: {network_stats['connection_quality']}", font=small_font, fill=quality_color)
            draw.text((10, 160), f"IP: {network_stats['external_ip']}", font=small_font, fill=config.COLOR_TITLE)
            
            # Draw the ping graph
            draw_ping_graph(draw, small_font)
            
            # Draw packet loss at the bottom
            draw.text(
                (10 + 300 + 10, 170 + 60 - 10),  # Using fixed positions
                f"Loss: {network_stats['packet_loss']:.1f}%",
                font=small_font,
                fill=config.COLOR_LOSS
            )
            
            display_output.display(image, network_stats)
        else:
            # In test mode output
            current_time = time.time()
            if current_time - display_output.last_print_time >= get('display_refresh'):
                quality_face = get_quality_face(network_stats['connection_quality'])
                print("\033[2J\033[H")  # Clear screen and move cursor to top
                print("=== Network Monitor ===")
                print(f"Connection Status: {quality_face}")
                print(f"External IP: {network_stats['external_ip']}")
                print(f"Download: {network_stats['download']:.1f} Mbps")
                print(f"Upload: {network_stats['upload']:.1f} Mbps")
                print(f"Ping: {network_stats['ping']:.0f} ms")
                print(f"Jitter: {network_stats['jitter']:.1f} ms")
                print(f"Packet Loss: {network_stats['packet_loss']:.1f}%")
                print(f"Connection Quality: {network_stats['connection_quality']}")
                print("\n=== Ping History ===")
                if ping_history:
                    print(f"Min: {min(ping_history):.0f}ms Max: {max(ping_history):.0f}ms")
                else:
                    print("Collecting ping data...")
                print("=====================")
                display_output.last_print_time = current_time
            
            display_output.display(None, network_stats)
        
        time.sleep(get('display_refresh'))

def monitor_config():
    """Monitor config file for changes"""
    last_check = 0
    while True:
        try:
            current_time = time.time()
            if current_time - last_check >= 1:  # Check once per second
                config.config.check_for_updates()
                last_check = current_time
        except Exception as e:
            print(f"Error monitoring config: {e}")
        time.sleep(1)

def main():
    # Create and start threads for each monitoring function
    speed_thread = threading.Thread(target=run_speed_test, daemon=True)
    ping_thread = threading.Thread(target=check_ping_and_packet_loss, daemon=True)
    display_thread = threading.Thread(target=update_display, daemon=True)
    ip_thread = threading.Thread(target=check_external_ip, daemon=True)
    config_thread = threading.Thread(target=monitor_config, daemon=True)  # Add config monitoring thread

    speed_thread.start()
    ping_thread.start()
    display_thread.start()
    ip_thread.start()
    config_thread.start()  # Start config monitoring thread

    # Keep the main thread running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")

if __name__ == "__main__":
    main()
