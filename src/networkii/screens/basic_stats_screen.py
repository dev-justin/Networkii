from PIL import Image
from .base_screen import BaseScreen
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, COLORS

class BasicStatsScreen(BaseScreen):
    def draw(self, stats: NetworkStats):
        """Show current network statistics with large text in a 2x2 grid."""
        self.clear_screen()
        
        # Calculate health score and get face
        health_score, health_state = self.display.calculate_network_health(stats)
        
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
        
        # Draw metrics in other grid cells
        self._draw_metric("PING", stats.ping, COLORS['green'], 1, 0)  # top-right
        self._draw_metric("JITTER", stats.jitter, COLORS['red'], 0, 1)  # bottom-left
        self._draw_metric("LOSS", stats.packet_loss, COLORS['purple'], 1, 1)  # bottom-right
        
        self.update_display()
    
    def _draw_metric(self, label: str, value: float, color: tuple, grid_x: int, grid_y: int):
        """Draw a metric in a grid cell."""
        # Calculate cell center
        GRID_WIDTH = SCREEN_WIDTH // 2
        GRID_HEIGHT = SCREEN_HEIGHT // 2
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
    
    def handle_button(self, button_label):
        # Basic stats screen might use buttons for navigation
        pass 