from PIL import Image
import time
from .base_screen import BaseScreen
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, COLORS

class SetupScreen(BaseScreen):
    def __init__(self, display):
        super().__init__(display)
        self.last_face_change = time.time()
        self.face_types = ['excellent', 'good', 'fair', 'poor', 'critical']
        self.current_face_index = 0
        
    def draw_screen(self, stats: NetworkStats = None):
        """Show the setup screen with simple instructions."""
        self.clear_screen()
        
        # Draw welcome message
        message = "Hey! I'm Networkii"
        message_bbox = self.draw.textbbox((0, 0), message, font=self.font_lg)
        message_width = message_bbox[2] - message_bbox[0]
        message_x = (SCREEN_WIDTH - message_width) // 2
        message_y = 20
        self.draw.text((message_x, message_y), message, font=self.font_lg, fill=COLORS['white'])
        
        # Check if it's time to change face
        current_time = time.time()
        if current_time - self.last_face_change >= 1.0:  # Change face every second
            self.current_face_index = (self.current_face_index + 1) % len(self.face_types)
            self.last_face_change = current_time
        
        # Draw current face (centered, 75% of original size)
        face_type = self.face_types[self.current_face_index]
        face = self.face_images[face_type]
        face_size = int(FACE_SIZE * 0.75)  # Make face 75% of original size
        resized_face = face.resize((face_size, face_size), Image.Resampling.LANCZOS)
        face_x = (SCREEN_WIDTH - face_size) // 2
        face_y = (SCREEN_HEIGHT - face_size) // 2 - 10
        self.image.paste(resized_face, (face_x, face_y), resized_face)
        
        # Draw setup instructions on two lines
        line1 = "Setup by visiting:"
        line2 = "ovvys.com/networkii"
        
        # Calculate positions for both lines
        line1_bbox = self.draw.textbbox((0, 0), line1, font=self.font_md)
        line2_bbox = self.draw.textbbox((0, 0), line2, font=self.font_lg)  # Larger font for URL
        
        line1_width = line1_bbox[2] - line1_bbox[0]
        line2_width = line2_bbox[2] - line2_bbox[0]
        
        # Calculate heights for vertical centering
        line1_height = line1_bbox[3] - line1_bbox[1]
        line2_height = line2_bbox[3] - line2_bbox[1]
        
        # Position text at bottom with small spacing
        line_spacing = 12  # Reduced spacing between lines
        total_height = line1_height + line2_height + line_spacing
        start_y = SCREEN_HEIGHT - total_height - 15  # Start 15px from bottom
        
        # Draw each line centered
        self.draw.text(
            ((SCREEN_WIDTH - line1_width) // 2, start_y),
            line1,
            font=self.font_md,
            fill=COLORS['white']
        )
        
        self.draw.text(
            ((SCREEN_WIDTH - line2_width) // 2, start_y + line1_height + line_spacing),
            line2,
            font=self.font_lg,
            fill=COLORS['green']
        )
        
        self.update_display()
    
    def handle_button(self, button_label):
        # Setup screen might not need button handling
        pass 