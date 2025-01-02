import logging
import os
from pathlib import Path
from displayhatmini import DisplayHATMini
from PIL import Image, ImageDraw, ImageFont
from ..config import (SCREEN_WIDTH, SCREEN_HEIGHT, FONT_XS, FONT_SM, FONT_MD, 
                     FONT_LG, FONT_XL, HEALTH_THRESHOLDS, FACE_SIZE, HEART_SIZE, 
                     RECENT_HISTORY_LENGTH, COLORS, HEART_GAP, METRIC_TOP_MARGIN, 
                     METRIC_BOTTOM_MARGIN, METRIC_WIDTH) 
from ..models.network_stats import NetworkStats, NetworkMetrics
from collections import deque
import statistics

logger = logging.getLogger('display')

# Display class for shared resources and methods
class Display:
    def __init__(self):
        # Initialize display buffer
        self.image = Image.new('RGB', (SCREEN_WIDTH, SCREEN_HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        # Initialize display with buffer
        self.disp = DisplayHATMini(self.image)
                
        # Load fonts
        self.font_xs = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_XS)
        self.font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_SM)
        self.font_md = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_MD)
        self.font_lg = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_LG)
        self.font_xl = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", FONT_XL)

        # Load face images
        self.face_images = {}
        base_dir = Path.home() / 'Networkii'
        for state, info in HEALTH_THRESHOLDS.items():
            image_path = base_dir / info['face']
            logger.info(f"Loading face image from: {image_path}")
            image = Image.open(image_path).convert('RGBA')
            self.face_images[state] = image.resize((FACE_SIZE, FACE_SIZE), Image.Resampling.LANCZOS)

        # Load heart image
        heart_path = base_dir / 'assets' / 'heart.png'
        logger.info(f"Loading heart image from: {heart_path}")
        self.heart_image = Image.open(heart_path).convert('RGBA')
        self.heart_image = self.heart_image.resize((HEART_SIZE, HEART_SIZE))

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
        
        # Get last 8 historical values (excluding current)
        last_values = list(history)[-9:-1]  # Get 8 values before the current
        if not last_values:
            return
            
        # Calculate spacing between values
        history_start_x = LABEL_WIDTH + CURRENT_WIDTH + 10  # Start after current value
        history_area_width = SCREEN_WIDTH - history_start_x - RIGHT_MARGIN
        value_spacing = min(40, history_area_width // len(last_values))  # Cap spacing at 40px
        
        # Draw values from recent to old (left to right)
        for i, value in enumerate(reversed(last_values)):  # Reverse to show recent first
            fade_level = 0.7 - (i * 0.08)  # Fade gets stronger towards the right
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
