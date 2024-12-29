import time
import statistics
from collections import deque
from PIL import Image, ImageDraw, ImageFont
from displayhatmini import DisplayHATMini
from ..models.network_stats import NetworkStats
from ..utils.metrics import NetworkMetrics
from ..config import (SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, HEART_SIZE, 
                     HEART_SPACING, HEART_GAP, NETWORK_STATES,
                     FONT_LARGE, FONT_MEDIUM, FONT_SMALL, FONT_MESSAGE, FONT_TITLE,
                     RECENT_HISTORY_LENGTH, METRIC_WIDTH, METRIC_SPACING, 
                     METRIC_RIGHT_MARGIN, METRIC_TOP_MARGIN, METRIC_BOTTOM_MARGIN,
                     BAR_WIDTH, BAR_SPACING, BAR_START_X, HEALTH_THRESHOLDS, COLORS)

class Display:
    def __init__(self, network_monitor=None):
        
        self.network_monitor = network_monitor

        # Initialize display
        self.image = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.disp = DisplayHATMini(self.image)
        
        # Load fonts
        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_TITLE)
            self.tiny_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SMALL)
            self.number_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_LARGE)
            self.medium_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_MEDIUM)
            self.message_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_MESSAGE)
        except:
            self.font = ImageFont.load_default()
            self.tiny_font = ImageFont.load_default()
            self.number_font = ImageFont.load_default()
            self.medium_font = ImageFont.load_default()
            self.message_font = ImageFont.load_default()

        # Load face images
        self.face_images = {}
        for state, info in NETWORK_STATES.items():
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

    def calculate_network_health(self, stats: NetworkStats) -> tuple[int, str]:
        """Calculate network health based on recent history"""
        ping_history = list(stats.ping_history)[-RECENT_HISTORY_LENGTH:]
        jitter_history = list(stats.jitter_history)[-RECENT_HISTORY_LENGTH:]
        loss_history = list(stats.packet_loss_history)[-RECENT_HISTORY_LENGTH:]
        
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
        
        state = next((state for state, info in NETWORK_STATES.items() if final_score >= info['threshold']), 'critical')
        
        return int(final_score), state

    def calculate_bar_height(self, values: deque, metric_type: str) -> float:
        """Calculate health bar height based on historical values"""
        if not values:
            return 1.0
        threshold = NetworkMetrics.get_health_threshold(metric_type)
        bad_count = sum(1 for v in values if v > threshold)
        return 1.0 - (bad_count / len(values))

    def draw_health_bar(self, x: int, y: int, width: int, height: int, health: float, metric_type: str):
        """Draw a retro-style health bar"""
        color = COLORS[metric_type]
        dim_color = tuple(max(0, c // 3) for c in color)
        
        self.draw.rectangle(
            (x - 2, y - 2, x + width + 2, y + height + 2),
            outline=COLORS['border'],
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

    def draw_metric(self, x: int, y: int, label: str, history: deque, metric_type: str):
        """Draw metric column with values using full height"""
        if not history:
            return
            
        color = COLORS[metric_type]
        
        label_bbox = self.draw.textbbox((0, 0), label, font=self.tiny_font)
        label_width = label_bbox[2] - label_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - label_width) // 2, METRIC_TOP_MARGIN),
            label,
            font=self.tiny_font,
            fill=color
        )
        
        last_values = list(history)[-10:]
        if len(last_values) < 10:
            last_values = [0] * (10 - len(last_values)) + last_values
        
        available_height = SCREEN_HEIGHT - METRIC_TOP_MARGIN - METRIC_BOTTOM_MARGIN
        value_spacing = (available_height - 45) // 9
        
        current_value = str(round(last_values[-1]))
        current_bbox = self.draw.textbbox((0, 0), current_value, font=self.number_font)
        current_width = current_bbox[2] - current_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - current_width) // 2, METRIC_TOP_MARGIN + 20),
            current_value,
            font=self.number_font,
            fill=color
        )
        
        for i, value in enumerate(reversed(last_values[:-1]), 1):
            fade_level = 0.8 - (i * 0.08)
            faded_color = tuple(int(c * fade_level) for c in color)
            
            value_text = str(round(value))
            text_bbox = self.draw.textbbox((0, 0), value_text, font=self.medium_font)
            text_width = text_bbox[2] - text_bbox[0]
            
            text_x = x + (METRIC_WIDTH - text_width) // 2
            text_y = METRIC_TOP_MARGIN + 30 + (i * value_spacing)
            
            self.draw.text(
                (text_x, text_y),
                value_text,
                font=self.medium_font,
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
        
        self.draw_metric(metrics_x, 0, "P", stats.ping_history, 'ping')
        self.draw_metric(metrics_x + METRIC_WIDTH + METRIC_SPACING, 0, "J", stats.jitter_history, 'jitter')
        self.draw_metric(metrics_x + (METRIC_WIDTH + METRIC_SPACING) * 2, 0, "L", stats.packet_loss_history, 'packet_loss')
        
        message_bbox = self.draw.textbbox((0, 0), "Test", font=self.tiny_font)
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
        message = NETWORK_STATES[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.message_font)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = face_x + (FACE_SIZE - message_width) // 2
        self.draw.text((message_x, message_y), message, font=self.message_font, fill=(255, 255, 255))
        
        self.image.paste(self.face_images[health_state], (face_x, face_y), self.face_images[health_state])
        
        hearts_total_width = (5 * HEART_SIZE) + (4 * HEART_GAP)
        hearts_x = face_x + (FACE_SIZE - hearts_total_width) // 2
        self.draw_hearts(hearts_x, hearts_y, health_state)
        
        ping_health = self.calculate_bar_height(
            self.network_monitor.ping_history, 'ping')
        jitter_health = self.calculate_bar_height(
            self.network_monitor.jitter_history, 'jitter')
        loss_health = self.calculate_bar_height(
            self.network_monitor.packet_loss_history, 'packet_loss')
        
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
        SCORE_HEIGHT = self.message_font.size
        MESSAGE_HEIGHT = self.message_font.size
        
        total_height = SCORE_HEIGHT + SPACING + FACE_SIZE + SPACING + MESSAGE_HEIGHT
        start_y = (SCREEN_HEIGHT - total_height) // 2
        
        score_text = f"Health: {health_score}%"
        score_bbox = self.draw.textbbox((0, 0), score_text, font=self.message_font)
        score_width = score_bbox[2] - score_bbox[0]
        score_x = (SCREEN_WIDTH - score_width) // 2
        self.draw.text((score_x, start_y), score_text, font=self.message_font, fill=COLORS['text'])
        
        face = self.face_images[health_state]
        face_x = (SCREEN_WIDTH - FACE_SIZE) // 2
        face_y = start_y + SCORE_HEIGHT + SPACING
        self.image.paste(face, (face_x, face_y), face)
        
        message = NETWORK_STATES[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.message_font)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (SCREEN_WIDTH - message_width) // 2
        message_y = face_y + FACE_SIZE + SPACING
        self.draw.text((message_x, message_y), message, font=self.message_font, fill=(255, 255, 255))
        
        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)

    def show_detailed_screen(self, stats: NetworkStats):
        """Show detailed network statistics with history"""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
        
        TOP_MARGIN = 10
        ROW_SPACING = 2   
        LABEL_WIDTH = 80
        CURRENT_VALUE_SPACING = 8
        VALUE_WIDTH = SCREEN_WIDTH - LABEL_WIDTH - 20
        ROW_HEIGHT = 30
        
        def draw_metric_row(y: int, label: str, current_value: float, history: deque, color: tuple):
            self.draw.text((10, y), label, font=self.message_font, fill=color)
            
            current_text = str(round(current_value))
            current_bbox = self.draw.textbbox((0, 0), current_text, font=self.number_font)
            current_width = current_bbox[2] - current_bbox[0]
            self.draw.text(
                (LABEL_WIDTH - current_width + CURRENT_VALUE_SPACING, y),  
                current_text,
                font=self.number_font,
                fill=color
            )
            
            history_values = list(history)[-8:]
            value_spacing = VALUE_WIDTH // 8
            history_start_x = LABEL_WIDTH
            
            for i, value in enumerate(reversed(history_values[:-1]), 1):
                fade_level = 0.7 - (i * 0.08)
                faded_color = tuple(int(c * fade_level) for c in color)
                
                value_text = str(round(value))
                x_pos = history_start_x + (i * value_spacing)
                self.draw.text(
                    (x_pos, y + 5),
                    value_text,
                    font=self.tiny_font,
                    fill=faded_color
                )
        
        draw_metric_row(
            TOP_MARGIN,
            "PING",
            stats.ping,
            stats.ping_history,
            self.get_outline_color('ping')
        )
        
        draw_metric_row(
            TOP_MARGIN + ROW_HEIGHT + ROW_SPACING,
            "JITTER",
            stats.jitter,
            stats.jitter_history,
            self.get_outline_color('jitter')
        )
        
        draw_metric_row(
            TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 2,
            "LOSS",
            stats.packet_loss,
            stats.packet_loss_history,
            self.get_outline_color('packet_loss')
        )
        
        speed_y = TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 3 + 20
        if self.network_monitor.last_speed_test > 0:
            time_since_test = (time.time() - self.network_monitor.last_speed_test) / 60
            
            down_text = f"↓ {self.network_monitor.download_speed:.1f} Mbps"
            self.draw.text((10, speed_y), down_text, font=self.message_font, fill=COLORS['download'])
            
            up_text = f"↑ {self.network_monitor.upload_speed:.1f} Mbps"
            self.draw.text((10, speed_y + 30), up_text, font=self.message_font, fill=COLORS['upload'])
            
            time_text = f"Updated {int(time_since_test)}m ago"
            time_bbox = self.draw.textbbox((0, 0), time_text, font=self.tiny_font)
            time_width = time_bbox[2] - time_bbox[0]
            self.draw.text(
                (SCREEN_WIDTH - time_width - 10, speed_y + 15),
                time_text,
                font=self.tiny_font,
                fill=COLORS['time']
            )
        else:
            self.draw.text((10, speed_y), "Speed test pending...", font=self.tiny_font, fill=(255, 255, 255))
        
        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image) 