from PIL import Image
from .base_screen import BaseScreen
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, COLORS

class SetupScreen(BaseScreen):
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
        
        # Draw face (centered, smaller size)
        face = self.face_images['excellent']
        small_face_size = FACE_SIZE // 2  # Make face 50% smaller
        small_face = face.resize((small_face_size, small_face_size), Image.Resampling.LANCZOS)
        face_x = (SCREEN_WIDTH - small_face_size) // 2
        face_y = (SCREEN_HEIGHT - small_face_size) // 2 - 20
        self.image.paste(small_face, (face_x, face_y), small_face)
        
        # Draw setup instructions on three lines
        line1 = "Go to"
        line2 = "ovvys.com/networkii"
        line3 = "to setup!"
        
        # Calculate positions for all lines to be centered
        line1_bbox = self.draw.textbbox((0, 0), line1, font=self.font_md)
        line2_bbox = self.draw.textbbox((0, 0), line2, font=self.font_lg)  # Note larger font
        line3_bbox = self.draw.textbbox((0, 0), line3, font=self.font_md)
        
        line1_width = line1_bbox[2] - line1_bbox[0]
        line2_width = line2_bbox[2] - line2_bbox[0]
        line3_width = line3_bbox[2] - line3_bbox[0]
        
        # Calculate heights for vertical centering
        line1_height = line1_bbox[3] - line1_bbox[1]
        line2_height = line2_bbox[3] - line2_bbox[1]
        line3_height = line3_bbox[3] - line3_bbox[1]
        
        # Adjust spacing and positioning
        line_spacing = 15  # Reduced spacing between lines
        total_height = line1_height + line2_height + line3_height + (line_spacing * 2)
        start_y = SCREEN_HEIGHT - total_height - 20  # Start closer to bottom
        
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
        
        self.draw.text(
            ((SCREEN_WIDTH - line3_width) // 2, start_y + line1_height + line2_height + (line_spacing * 2)),
            line3,
            font=self.font_md,
            fill=COLORS['white']
        )
        
        self.update_display()
    
    def handle_button(self, button_label):
        # Setup screen might not need button handling
        pass 