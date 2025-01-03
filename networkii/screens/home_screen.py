from .base_screen import BaseScreen, logger
from ..models.network_stats import NetworkStats
from ..config import (SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, HEART_SIZE, 
                     HEART_SPACING, HEART_GAP, METRIC_WIDTH, METRIC_SPACING,
                     METRIC_RIGHT_MARGIN, BAR_WIDTH, BAR_SPACING, BAR_START_X,
                     COLORS, METRIC_TOP_MARGIN, METRIC_BOTTOM_MARGIN,
                     HEALTH_THRESHOLDS)

class HomeScreen(BaseScreen):
    def draw_screen(self, stats: NetworkStats):
        """Draw the home screen with network metrics."""
        self.clear_screen()
        
        # Calculate layout
        health_bars_width = BAR_START_X + (BAR_WIDTH * 3) + (BAR_SPACING * 2)
        metrics_width = (3 * (METRIC_WIDTH + METRIC_SPACING)) + METRIC_RIGHT_MARGIN
        remaining_width = SCREEN_WIDTH - health_bars_width - metrics_width
        
        # Draw metrics columns
        metrics_x = SCREEN_WIDTH - metrics_width
        self.draw_metric_col(metrics_x, 0, "P", stats.ping_history, COLORS['green'])
        self.draw_metric_col(metrics_x + METRIC_WIDTH + METRIC_SPACING, 0, "J", stats.jitter_history, COLORS['red'])
        self.draw_metric_col(metrics_x + (METRIC_WIDTH + METRIC_SPACING) * 2, 0, "L", stats.packet_loss_history, COLORS['purple'])
        
        # Calculate vertical layout for face and hearts
        message_bbox = self.draw.textbbox((0, 0), "Test", font=self.font_xs)
        message_height = message_bbox[3] - message_bbox[1]
        total_element_height = message_height + 20 + FACE_SIZE + HEART_SPACING + HEART_SIZE
        
        start_y = (SCREEN_HEIGHT - total_element_height) // 2
        face_x = health_bars_width + (remaining_width - FACE_SIZE) // 2
        
        message_y = start_y
        face_y = message_y + message_height + 20
        hearts_y = face_y + FACE_SIZE + HEART_SPACING
        
        # Draw health status
        health_score, health_state = self.display.calculate_network_health(stats)
        message = HEALTH_THRESHOLDS[health_state]['message']
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_sm)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = face_x + (FACE_SIZE - message_width) // 2
        self.draw.text((message_x, message_y), message, font=self.font_sm, fill=COLORS['white'])
        
        # Draw face
        self.image.paste(self.face_images[health_state], (face_x, face_y), self.face_images[health_state])
        
        # Draw hearts
        hearts_total_width = (5 * HEART_SIZE) + (4 * HEART_GAP)
        hearts_x = face_x + (FACE_SIZE - hearts_total_width) // 2
        self.draw_hearts(hearts_x, hearts_y, health_state)
        
        # Draw health bars
        ping_health = self.display.calculate_bar_height(stats.ping_history, 'ping')
        jitter_health = self.display.calculate_bar_height(stats.jitter_history, 'jitter')
        loss_health = self.display.calculate_bar_height(stats.packet_loss_history, 'packet_loss')
        
        self.draw_health_bar(BAR_START_X, 0, BAR_WIDTH, SCREEN_HEIGHT, ping_health, 'ping')
        self.draw_health_bar(BAR_START_X + BAR_WIDTH + BAR_SPACING, 0, BAR_WIDTH, SCREEN_HEIGHT, jitter_health, 'jitter')
        self.draw_health_bar(BAR_START_X + (BAR_WIDTH + BAR_SPACING) * 2, 0, BAR_WIDTH, SCREEN_HEIGHT, loss_health, 'packet_loss')
        
        self.update_display()
    
    def draw_metric_col(self, x: int, y: int, label: str, history: list, color: tuple):
        """Draw metric column with values using full height."""
        if not history:
            return
        
        # Draw label
        label_bbox = self.draw.textbbox((0, 0), label, font=self.font_sm)
        label_width = label_bbox[2] - label_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - label_width) // 2, y + METRIC_TOP_MARGIN),
            label,
            font=self.font_sm,
            fill=color
        )
        
        # Get last 10 values
        last_values = list(history)[-10:]
        if len(last_values) < 10:
            last_values = [0] * (10 - len(last_values)) + last_values
        
        # Calculate spacing
        available_height = SCREEN_HEIGHT - (y + METRIC_TOP_MARGIN) - METRIC_BOTTOM_MARGIN
        value_spacing = (available_height - 45) // 9
        
        # Draw current value
        current_value = str(round(last_values[-1]))
        current_bbox = self.draw.textbbox((0, 0), current_value, font=self.font_md)
        current_width = current_bbox[2] - current_bbox[0]
        self.draw.text(
            (x + (METRIC_WIDTH - current_width) // 2, METRIC_TOP_MARGIN + 20),
            current_value,
            font=self.font_md,
            fill=color
        )
        
        # Draw history values
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
    
    def draw_hearts(self, x: int, y: int, health_state: str):
        """Draw hearts based on network state."""
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
    
    def draw_health_bar(self, x: int, y: int, width: int, height: int, health: float, metric_type: str):
        """Draw a retro-style health bar."""
        if metric_type == 'ping':
            color = COLORS['green']
        elif metric_type == 'jitter':
            color = COLORS['red']
        else:  # packet_loss
            color = COLORS['purple']
            
        dim_color = tuple(max(0, c // 3) for c in color)
        
        # Draw border
        self.draw.rectangle(
            (x - 2, y - 2, x + width + 2, y + height + 2),
            outline=COLORS['gray'],
            width=1
        )
        
        # Draw segments
        total_segments = 20
        segment_height = height // total_segments
        filled_segments = round(health * total_segments)
        
        # Draw dim background
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
        
        # Draw filled segments
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

    def handle_button(self, button_label):
        """Handle button presses for home screen."""        
        if button_label == "B":
            self.screen_manager.previous_screen()
        elif button_label == "Y":
            self.screen_manager.next_screen()