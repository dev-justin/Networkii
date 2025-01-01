import time
import statistics
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
from ..models.network_stats import NetworkStats
from ..utils.metrics import NetworkMetrics
from ..config import (SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, HEART_SIZE, 
                     HEART_SPACING, HEART_GAP, HEALTH_THRESHOLDS,
                     RECENT_HISTORY_LENGTH, METRIC_WIDTH, METRIC_SPACING, 
                     METRIC_RIGHT_MARGIN, METRIC_TOP_MARGIN, METRIC_BOTTOM_MARGIN,
                     BAR_WIDTH, BAR_SPACING, BAR_START_X, COLORS,
                     FONT_XS, FONT_SM, FONT_MD, FONT_LG, FONT_XL)
import RPi.GPIO as GPIO
import logging

logger = logging.getLogger('display')

class Display:
    def __init__(self):
        # Initialize display
        self.image = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.disp = DisplayHATMini(self.image)  # Exposed for button handling by NetworkiiApp
        
        # Load fonts
        self.font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_XS)
        self.font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SM)
        self.font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_MD)
        self.font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_LG)
        self.font_xl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_XL)

        # Load face images
        self.face_images = {}
        for state, info in HEALTH_THRESHOLDS.items():
            try:
                image = Image.open(info['face']).convert('RGBA')
                self.face_images[state] = image.resize((FACE_SIZE, FACE_SIZE), Image.Resampling.LANCZOS)
            except Exception as e:
                print(f"Error loading face {info['face']}: {e}")
                img = Image.new('RGBA', (FACE_SIZE, FACE_SIZE), (0, 0, 0, 0))
                draw = ImageDraw.Draw(img)
                draw.text((FACE_SIZE//2, FACE_SIZE//2), "?", fill=(255, 255, 255, 255))
                self.face_images[state] = img

        # Load heart image
        try:
            self.heart_image = Image.open('assets/heart.png').convert('RGBA')
            self.heart_image = self.heart_image.resize((HEART_SIZE, HEART_SIZE))
        except Exception as e:
            print(f"Error loading heart image: {e}")
            self.heart_image = Image.new('RGBA', (HEART_SIZE, HEART_SIZE), (0, 0, 0, 0))
            draw = ImageDraw.Draw(self.heart_image)
            draw.text((HEART_SIZE//2, HEART_SIZE//2), "♥", fill=(255, 0, 0, 255))

    # Calculate network health. [Used for: Face and Hearts] [Uses recent history]
    def calculate_network_health(self, stats: NetworkStats) -> tuple[int, str]:
        """Calculate network health based on recent history"""
        ping_history = list(stats.ping_history)[-RECENT_HISTORY_LENGTH:]
        jitter_history = list(stats.jitter_history)[-RECENT_HISTORY_LENGTH:]
        loss_history = list(stats.packet_loss_history)[-RECENT_HISTORY_LENGTH:]
        
        # Initialize scores
        ping_score = 0
        jitter_score = 0
        loss_score = 0
        
        if ping_history:
            ping_scores = [NetworkMetrics.calculate_metric_score(p, NetworkMetrics.PING) for p in ping_history]
            ping_score = statistics.mean(ping_scores) * NetworkMetrics.PING.weight
        
        if jitter_history:
            jitter_scores = [NetworkMetrics.calculate_metric_score(j, NetworkMetrics.JITTER) for j in jitter_history]
            jitter_score = statistics.mean(jitter_scores) * NetworkMetrics.JITTER.weight
            
        if loss_history:
            loss_scores = [NetworkMetrics.calculate_metric_score(l, NetworkMetrics.PACKET_LOSS) for l in loss_history]
            loss_score = statistics.mean(loss_scores) * NetworkMetrics.PACKET_LOSS.weight
        
        final_score = ping_score + jitter_score + loss_score
        final_score = max(0, min(100, final_score))
        
        state = next((state for state, info in HEALTH_THRESHOLDS.items() if final_score >= info['threshold']), 'critical')
        
        return int(final_score), state

    # Calculate health bar height. [Used for: Health Bars] [Uses full history]
    def calculate_bar_height(self, values: deque, metric_type: str) -> float:
        """Calculate health bar height based on historical values"""
        if not values:
            return 1.0
        threshold = NetworkMetrics.get_health_threshold(metric_type)
        bad_count = sum(1 for v in values if v > threshold)
        return 1.0 - (bad_count / len(values))

    # Draw health bar. [Used for: Health Bars]
    def draw_health_bar(self, x: int, y: int, width: int, height: int, health: float, metric_type: str):
        """Draw a retro-style health bar"""
        if metric_type == 'ping':
            color = COLORS['green']
        elif metric_type == 'jitter':
            color = COLORS['red']
        else:  # packet_loss
            color = COLORS['purple']
            
        dim_color = tuple(max(0, c // 3) for c in color)
        
        self.draw.rectangle(
            (x - 2, y - 2, x + width + 2, y + height + 2),
            outline=COLORS['gray'],
            width=1
        )
        
        total_segments = 20
        segment_height = height // total_segments
        filled_segments = round(health * total_segments)
        
        for i in range(total_segments):
            segment_y = y + height - ((i + 1) * segment_height)
            self.draw.rectangle(
                (x, segment_y, x + width, segment_y + segment_height - 1),
                fill=dim_color
            )
            self.draw.line(
                (x, segment_y, x + width, segment_y),
                fill=(0, 0, 0),
                width=1
            )
        
        if filled_segments > 0:
            fill_height = filled_segments * segment_height
            self.draw.rectangle(
                (x, y + height - fill_height, x + width, y + height),
                fill=color
            )
            
            for i in range(filled_segments):
                line_y = y + height - ((i + 1) * segment_height)
                self.draw.line(
                    (x, line_y, x + width, line_y),
                    fill=(0, 0, 0),
                    width=1
                )

    # Draw hearts. [Used for: Hearts]
    def draw_hearts(self, x: int, y: int, health_state: str):
        """Draw hearts based on network state"""
        total_hearts = 5
        filled_hearts = HEALTH_THRESHOLDS[health_state]['hearts']
        
        for i in range(total_hearts):
            heart_x = x + (i * (HEART_SIZE + HEART_GAP))
            if i < filled_hearts:
                self.image.paste(self.heart_image, (heart_x, y), self.heart_image)
            else:
                heart_outline = self.heart_image.copy()
                heart_outline.putalpha(50)
                self.image.paste(heart_outline, (heart_x, y), heart_outline)

    def draw_metric_col(self, x: int, y: int, label: str, history: deque, color: tuple):
        """Draw metric column with values using full height"""
        if not history:
            return
        
        label_bbox = self.draw.textbbox((0, 0), label, font=self.font_sm)
        label_width = label_bbox[2] - label_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - label_width) // 2, y + METRIC_TOP_MARGIN),
            label,
            font=self.font_sm,
            fill=color
        )
        
        last_values = list(history)[-10:]
        if len(last_values) < 10:
            last_values = [0] * (10 - len(last_values)) + last_values
        
        available_height = SCREEN_HEIGHT - (y + METRIC_TOP_MARGIN) - METRIC_BOTTOM_MARGIN
        value_spacing = (available_height - 45) // 9
        
        current_value = str(round(last_values[-1]))
        current_bbox = self.draw.textbbox((0, 0), current_value, font=self.font_md)
        current_width = current_bbox[2] - current_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - current_width) // 2, METRIC_TOP_MARGIN + 20),
            current_value,
            font=self.font_md,
            fill=color
        )
        
        for i, value in enumerate(reversed(last_values[:-1]), 1):
            fade_level = 0.8 - (i * 0.08)
            faded_color = tuple(int(c * fade_level) for c in color)
            
            value_text = str(round(value))
            text_bbox = self.draw.textbbox((0, 0), value_text, font=self.font_sm)
            text_width = text_bbox[2] - text_bbox[0]
            
            text_x = x + (METRIC_WIDTH - text_width) // 2
            text_y = METRIC_TOP_MARGIN + 30 + (i * value_spacing)
            
            self.draw.text(
                (text_x, text_y),
                value_text,
                font=self.font_sm,
                fill=faded_color
            )

    def draw_metric_row(self, y: int, label: str, current_value: float, history: deque, color: tuple):
        """Draw metric row with historical values"""
        LABEL_WIDTH = 60  # Reduced to give more space
        CURRENT_WIDTH = 50  # Fixed width for current value
        RIGHT_MARGIN = 5
        
        # Draw label
        self.draw.text((10, y), label, font=self.font_sm, fill=color)
        
        # Draw current value with larger font
        current_text = str(round(current_value))
        current_bbox = self.draw.textbbox((0, 0), current_text, font=self.font_lg)
        current_width = current_bbox[2] - current_bbox[0]
        current_x = LABEL_WIDTH + (CURRENT_WIDTH - current_width) // 2
        self.draw.text(
            (current_x, y - 5),  # Adjust y position for larger font
            current_text,
            font=self.font_lg,
            fill=color
        )
        
        # Get last 8 historical values
        history_values = list(history)[-8:]
        if len(history_values) > 1:  # Only draw history if we have values
            history_values = history_values[:-1]  # Exclude current value
            
            # Calculate spacing between values
            total_values = len(history_values)
            if total_values > 0:
                # Calculate the space available for historical values
                history_start_x = LABEL_WIDTH + CURRENT_WIDTH + 10  # Start after current value
                history_area_width = SCREEN_WIDTH - history_start_x - RIGHT_MARGIN
                value_spacing = min(40, history_area_width // total_values)  # Cap spacing at 40px
                
                # Draw values left to right
                for i, value in enumerate(history_values):
                    fade_level = 0.7 - ((total_values - i - 1) * 0.08)  # Fade gets stronger towards the right
                    faded_color = tuple(int(c * fade_level) for c in color)
                    
                    value_text = str(round(value))
                    text_bbox = self.draw.textbbox((0, 0), value_text, font=self.font_md)
                    text_width = text_bbox[2] - text_bbox[0]
                    
                    # Position each value from left to right
                    x_pos = history_start_x + (i * value_spacing)
                    x_pos = x_pos + (value_spacing - text_width) // 2  # Center in available space
                    
                    self.draw.text(
                        (x_pos, y),
                        value_text,
                        font=self.font_md,
                        fill=faded_color
                    )

    def show_home_screen(self, stats: NetworkStats):
        """Update the home screen with network metrics"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        health_bars_width = BAR_START_X + (BAR_WIDTH * 3) + (BAR_SPACING * 2)
        metrics_width = (3 * (METRIC_WIDTH + METRIC_SPACING)) + METRIC_RIGHT_MARGIN
        remaining_width = SCREEN_WIDTH - health_bars_width - metrics_width
        
        face_x = health_bars_width + (remaining_width - FACE_SIZE) // 2
        face_y = (SCREEN_HEIGHT - (FACE_SIZE + HEART_SIZE + HEART_SPACING)) // 2
        
        metrics_x = SCREEN_WIDTH - metrics_width
        
        self.draw_metric_col(metrics_x, 0, "P", stats.ping_history, COLORS['green'])
        self.draw_metric_col(metrics_x + METRIC_WIDTH + METRIC_SPACING, 0, "J", stats.jitter_history, COLORS['red'])
        self.draw_metric_col(metrics_x + (METRIC_WIDTH + METRIC_SPACING) * 2, 0, "L", stats.packet_loss_history, COLORS['purple'])
        
        message_bbox = self.draw.textbbox((0, 0), "Test", font=self.font_xs)
        message_height = message_bbox[3] - message_bbox[1]
        total_element_height = (
            message_height +
            20 +
            FACE_SIZE +
            HEART_SPACING +
            HEART_SIZE
        )
        
        start_y = (SCREEN_HEIGHT - total_element_height) // 2
        
        message_y = start_y
        face_y = message_y + message_height + 20
        hearts_y = face_y + FACE_SIZE + HEART_SPACING
        
        health_score, health_state = self.calculate_network_health(stats)
        message = HEALTH_THRESHOLDS[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_sm)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = face_x + (FACE_SIZE - message_width) // 2
        self.draw.text((message_x, message_y), message, font=self.font_sm, fill=(255, 255, 255))
        
        self.image.paste(self.face_images[health_state], (face_x, face_y), self.face_images[health_state])
        
        hearts_total_width = (5 * HEART_SIZE) + (4 * HEART_GAP)
        hearts_x = face_x + (FACE_SIZE - hearts_total_width) // 2
        self.draw_hearts(hearts_x, hearts_y, health_state)
        
        ping_health = self.calculate_bar_height(
            stats.ping_history, 'ping')
        jitter_health = self.calculate_bar_height(
            stats.jitter_history, 'jitter')
        loss_health = self.calculate_bar_height(
            stats.packet_loss_history, 'packet_loss')
        
        self.draw_health_bar(BAR_START_X, 0, BAR_WIDTH, SCREEN_HEIGHT, ping_health, 'ping')
        self.draw_health_bar(BAR_START_X + BAR_WIDTH + BAR_SPACING, 0, BAR_WIDTH, SCREEN_HEIGHT, jitter_health, 'jitter')
        self.draw_health_bar(BAR_START_X + (BAR_WIDTH + BAR_SPACING) * 2, 0, BAR_WIDTH, SCREEN_HEIGHT, loss_health, 'packet_loss')

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def show_basic_screen(self, stats: NetworkStats):
        """Show the status screen with face and network state"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        health_score, health_state = self.calculate_network_health(stats)
        
        SPACING = 20
        SCORE_HEIGHT = self.font_sm.size
        MESSAGE_HEIGHT = self.font_sm.size
        
        total_height = SCORE_HEIGHT + SPACING + FACE_SIZE + SPACING + MESSAGE_HEIGHT
        start_y = (SCREEN_HEIGHT - total_height) // 2
        
        score_text = f"Health: {health_score}%"
        score_bbox = self.draw.textbbox((0, 0), score_text, font=self.font_md)
        score_width = score_bbox[2] - score_bbox[0]
        score_x = (SCREEN_WIDTH - score_width) // 2
        self.draw.text((score_x, start_y), score_text, font=self.font_md, fill=COLORS['white'])
        
        face = self.face_images[health_state]
        face_x = (SCREEN_WIDTH - FACE_SIZE) // 2
        face_y = start_y + SCORE_HEIGHT + SPACING
        self.image.paste(face, (face_x, face_y), face)
        
        message = HEALTH_THRESHOLDS[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_sm)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (SCREEN_WIDTH - message_width) // 2
        message_y = face_y + FACE_SIZE + SPACING
        self.draw.text((message_x, message_y), message, font=self.font_sm, fill=COLORS['white'])

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def show_detailed_screen(self, stats: NetworkStats):
        """Show detailed network statistics with history"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        TOP_MARGIN = 10
        ROW_SPACING = 2   
        ROW_HEIGHT = 30
        
        self.draw_metric_row(
            TOP_MARGIN,
            "PING",
            stats.ping,
            stats.ping_history,
            COLORS['green']
        )
        
        self.draw_metric_row(
            TOP_MARGIN + ROW_HEIGHT + ROW_SPACING,
            "JITTER",
            stats.jitter,
            stats.jitter_history,
            COLORS['red']
        )
        
        self.draw_metric_row(
            TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 2,
            "LOSS",
            stats.packet_loss,
            stats.packet_loss_history,
            COLORS['purple']
        )
        
        speed_y = TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 3 + 10
        if stats.speed_test_status:
            status_text = f"Speed test in progress..."
            self.draw.text((10, speed_y), status_text, font=self.font_sm, fill=COLORS['white'])
            
        elif stats.speed_test_timestamp > 0:
            time_since_test = (time.time() - stats.speed_test_timestamp) / 60
            
            down_text = f"↓ {stats.download_speed:.1f} Mbps"
            self.draw.text((10, speed_y), down_text, font=self.font_sm, fill=COLORS['green'])
            
            up_text = f"↑ {stats.upload_speed:.1f} Mbps"
            self.draw.text((10, speed_y + 30), up_text, font=self.font_sm, fill=COLORS['red'])
            
            time_text = f"Updated {int(time_since_test)}m ago"
            time_bbox = self.draw.textbbox((0, 0), time_text, font=self.font_xs)
            time_width = time_bbox[2] - time_bbox[0]
            self.draw.text(
                (SCREEN_WIDTH - time_width - 10, speed_y + 15),
                time_text,
                font=self.font_xs,
                fill=COLORS['purple']
            )
        else:
            self.draw.text((10, speed_y), "Speed test pending...", font=self.font_xs, fill=COLORS['white'])

        # Draw interface info at bottom with divider
        bottom_y = SCREEN_HEIGHT - 45
        self.draw.line([(10, bottom_y), (SCREEN_WIDTH - 10, bottom_y)], fill=COLORS['gray'], width=1)
        
        # Interface info with colored labels
        interface_y = bottom_y + 5
        self.draw.text((10, interface_y), "Interface:", font=self.font_md, fill=COLORS['purple'])
        interface_text = f"{stats.interface} ({stats.interface_ip})"
        interface_bbox = self.draw.textbbox((0, 0), "Interface:", font=self.font_md)
        interface_width = interface_bbox[2] - interface_bbox[0]
        self.draw.text((20 + interface_width, interface_y), interface_text, font=self.font_md, fill=COLORS['white'])
        
        # Target info
        target_y = interface_y + 20
        self.draw.text((10, target_y), "Target:", font=self.font_md, fill=COLORS['green'])
        target_bbox = self.draw.textbbox((0, 0), "Target:", font=self.font_md)
        target_width = target_bbox[2] - target_bbox[0]
        self.draw.text((20 + target_width, target_y), stats.ping_target, font=self.font_md, fill=COLORS['white'])

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def show_no_connection_screen(self):
        """Show the no connection screen with AP mode instructions"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        # Draw welcome message with larger font
        message = "Welcome! I'm Networkii"
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_lg)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (SCREEN_WIDTH - message_width) // 2
        message_y = 15  # Slightly more top margin
        self.draw.text((message_x, message_y), message, font=self.font_lg, fill=COLORS['white'])
        
        # Calculate center position for smaller face (2/3 of original size)
        small_face_size = (FACE_SIZE * 2) // 3  # Integer division for 2/3 size
        face = self.face_images['excellent'].resize((small_face_size, small_face_size), Image.Resampling.LANCZOS)
        face_x = (SCREEN_WIDTH - small_face_size) // 2
        face_y = message_y + 35  # More space after larger title
        self.image.paste(face, (face_x, face_y), face)
        
        # Draw divider line
        divider_y = face_y + small_face_size + 20  # More space before divider
        self.draw.line([(20, divider_y), (SCREEN_WIDTH - 20, divider_y)], fill=COLORS['gray'], width=1)
        
        # Start content after divider
        content_y = divider_y + 25
        
        # Find the widest instruction to align both rows
        instructions1 = "1. Connect to WiFi:"
        instructions2 = "2. Then Visit:"
        instructions1_bbox = self.draw.textbbox((0, 0), instructions1, font=self.font_md)
        instructions2_bbox = self.draw.textbbox((0, 0), instructions2, font=self.font_md)
        instruction_width = max(instructions1_bbox[2], instructions2_bbox[2])
        
        # Calculate left margin to center the entire content block
        ssid = "Networkii"
        url = "networkii.local"
        ssid_bbox = self.draw.textbbox((0, 0), ssid, font=self.font_sm)
        url_bbox = self.draw.textbbox((0, 0), url, font=self.font_sm)
        max_value_width = max(ssid_bbox[2], url_bbox[2])
        total_width = instruction_width + 15 + max_value_width  # 15px spacing between text
        left_margin = (SCREEN_WIDTH - total_width) // 2
        
        # Draw first row
        self.draw.text((left_margin, content_y), instructions1, font=self.font_md, fill=COLORS['white'])
        self.draw.text((left_margin + instruction_width + 15, content_y), ssid, font=self.font_sm, fill=COLORS['green'])
        
        # Draw second row
        web_instructions_y = content_y + 30  # Reduced spacing between rows
        self.draw.text((left_margin, web_instructions_y), instructions2, font=self.font_md, fill=COLORS['white'])
        self.draw.text((left_margin + instruction_width + 15, web_instructions_y), url, font=self.font_sm, fill=COLORS['red'])

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image) 

    def show_no_internet_screen(self):
        """Show the no internet screen"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        # Draw title with reduced top margin
        title = "No Internet Connection"
        title_bbox = self.draw.textbbox((0, 0), title, font=self.font_lg)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (SCREEN_WIDTH - title_width) // 2
        title_y = 10
        self.draw.text((title_x, title_y), title, font=self.font_lg, fill=COLORS['red'])
        
        # Draw smaller sad face
        face = self.face_images['critical'].resize(((FACE_SIZE * 2) // 3, (FACE_SIZE * 2) // 3), Image.Resampling.LANCZOS)
        face_x = (SCREEN_WIDTH - face.size[0]) // 2
        face_y = title_y + 30
        self.image.paste(face, (face_x, face_y), face)
        
        # Draw divider
        divider_y = face_y + face.size[1] + 15
        self.draw.line([(20, divider_y), (SCREEN_WIDTH - 20, divider_y)], fill=COLORS['gray'], width=1)
        
        # Draw messages
        message = "Connected to WiFi but"
        message2 = "can't reach the internet"
        message_y = divider_y + 15
        
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_md)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (SCREEN_WIDTH - message_width) // 2
        self.draw.text((message_x, message_y), message, font=self.font_md, fill=COLORS['white'])
        
        message2_bbox = self.draw.textbbox((0, 0), message2, font=self.font_md)
        message2_width = message2_bbox[2] - message2_bbox[0]
        message2_x = (SCREEN_WIDTH - message2_width) // 2
        self.draw.text((message2_x, message_y + 20), message2, font=self.font_md, fill=COLORS['white'])
        
        # Draw instruction
        instruction = "Press B to try new WiFi"
        instruction_bbox = self.draw.textbbox((0, 0), instruction, font=self.font_md)
        instruction_width = instruction_bbox[2] - instruction_bbox[0]
        instruction_x = (SCREEN_WIDTH - instruction_width) // 2
        instruction_y = message_y + 55
        self.draw.text((instruction_x, instruction_y), instruction, font=self.font_md, fill=COLORS['green'])

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image) 

    def show_basic_stats_screen(self, stats: NetworkStats):
        """Show current network statistics with large text in a 2x2 grid"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        # Calculate health score and get face
        health_score, health_state = self.calculate_network_health(stats)
        
        # Setup grid
        GRID_MARGIN = 10
        GRID_WIDTH = SCREEN_WIDTH // 2
        GRID_HEIGHT = SCREEN_HEIGHT // 2
        
        # Draw face in top-left
        face_size = min(GRID_WIDTH - GRID_MARGIN * 2, GRID_HEIGHT - GRID_MARGIN * 2)
        face = self.face_images[health_state].resize((face_size, face_size), Image.Resampling.LANCZOS)
        face_x = (GRID_WIDTH - face_size) // 2
        face_y = (GRID_HEIGHT - face_size) // 2
        self.image.paste(face, (face_x, face_y), face)
        
        # Function to draw metric in a grid cell
        def draw_metric(label, value, color, grid_x, grid_y):
            # Calculate cell center
            cell_x = grid_x * GRID_WIDTH
            cell_y = grid_y * GRID_HEIGHT
            cell_center_x = cell_x + GRID_WIDTH // 2
            cell_center_y = cell_y + GRID_HEIGHT // 2
            
            # Draw label
            label_bbox = self.draw.textbbox((0, 0), label, font=self.font_lg)
            label_width = label_bbox[2] - label_bbox[0]
            label_x = cell_center_x - label_width // 2
            self.draw.text((label_x, cell_center_y - 30), label, font=self.font_lg, fill=color)
            
            # Draw value
            value_text = str(round(value))
            value_bbox = self.draw.textbbox((0, 0), value_text, font=self.font_xl)
            value_width = value_bbox[2] - value_bbox[0]
            value_x = cell_center_x - value_width // 2
            self.draw.text((value_x, cell_center_y + 5), value_text, font=self.font_xl, fill=color)
        
        # Draw metrics in other grid cells
        # Ping in top-right (1, 0)
        draw_metric("PING", stats.ping, COLORS['green'], 1, 0)
        
        # Jitter in bottom-left (0, 1)
        draw_metric("JITTER", stats.jitter, COLORS['red'], 0, 1)
        
        # Loss in bottom-right (1, 1)
        draw_metric("LOSS", stats.packet_loss, COLORS['purple'], 1, 1)

        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image) 