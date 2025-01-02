import time
from .base_screen import BaseScreen
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS

class DetailedStatsScreen(BaseScreen):
    def draw_screen(self, stats: NetworkStats):
        """Show detailed network statistics with history."""
        self.clear_screen()
        
        TOP_MARGIN = 10
        ROW_SPACING = 2   
        ROW_HEIGHT = 30
        
        # Draw metric rows
        self._draw_metric_row(
            TOP_MARGIN,
            "PING",
            stats.ping,
            stats.ping_history,
            COLORS['green']
        )
        
        self._draw_metric_row(
            TOP_MARGIN + ROW_HEIGHT + ROW_SPACING,
            "JITTER",
            stats.jitter,
            stats.jitter_history,
            COLORS['red']
        )
        
        self._draw_metric_row(
            TOP_MARGIN + (ROW_HEIGHT + ROW_SPACING) * 2,
            "LOSS",
            stats.packet_loss,
            stats.packet_loss_history,
            COLORS['purple']
        )
        
        # Draw speed test info
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
        
        self.update_display()
    
    def _draw_metric_row(self, y: int, label: str, current_value: float, history: list, color: tuple):
        """Draw metric row with historical values."""
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
    
    def handle_button(self, button_label):
        """Handle button presses for detailed stats screen."""
        if button_label == "A":
            # Go to previous screen
            self.screen_manager.previous_screen()
        elif button_label == "B":
            # Go to next screen
            self.screen_manager.next_screen()
        elif button_label == "X":
            # Return to basic stats
            self.screen_manager.switch_screen('basic_stats')
        elif button_label == "Y":
            # Return to home screen
            self.screen_manager.switch_screen('home') 