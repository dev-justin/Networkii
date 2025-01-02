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
        small_face = face.resize((small_face_size, small_face_size), Image.LANCZOS)
        face_x = (SCREEN_WIDTH - small_face_size) // 2
        face_y = (SCREEN_HEIGHT - small_face_size) // 2 - 20
        self.image.paste(small_face, (face_x, face_y), small_face)
        
        # Draw website URL with highlight color
        url = "Go to ovvys.com/networkii"
        url_bbox = self.draw.textbbox((0, 0), url, font=self.font_md)
        url_width = url_bbox[2] - url_bbox[0]
        url_x = (SCREEN_WIDTH - url_width) // 2
        url_y = SCREEN_HEIGHT - 60
        self.draw.text((url_x, url_y), url, font=self.font_md, fill=(64, 224, 208))  # Turquoise color
        
        # Draw setup text
        setup_text = "to setup"
        setup_bbox = self.draw.textbbox((0, 0), setup_text, font=self.font_md)
        setup_width = setup_bbox[2] - setup_bbox[0]
        setup_x = (SCREEN_WIDTH - setup_width) // 2
        setup_y = SCREEN_HEIGHT - 35
        self.draw.text((setup_x, setup_y), setup_text, font=self.font_md, fill=COLORS['white'])
        
        self.update_display()
    
    def handle_button(self, button_label):
        # Setup screen might not need button handling
        pass 