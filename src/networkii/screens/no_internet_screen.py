from PIL import Image
from .base_screen import BaseScreen
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT, FACE_SIZE, COLORS

class NoInternetScreen(BaseScreen):
    def draw(self, stats: NetworkStats = None):
        """Show the no internet screen."""
        self.clear_screen()
        
        # Draw title
        title = "No Internet"
        title_bbox = self.draw.textbbox((0, 0), title, font=self.font_xl)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (SCREEN_WIDTH - title_width) // 2
        title_y = 20
        self.draw.text((title_x, title_y), title, font=self.font_xl, fill=COLORS['red'])
        
        # Draw face (75% of original size)
        small_face_size = (FACE_SIZE * 3) // 4
        face = self.face_images['critical'].resize((small_face_size, small_face_size), Image.Resampling.LANCZOS)
        face_x = (SCREEN_WIDTH - small_face_size) // 2
        face_y = (SCREEN_HEIGHT - small_face_size) // 2 - 20
        self.image.paste(face, (face_x, face_y), face)
        
        # Draw instructions (split into two lines)
        question = "New WiFi?"
        question_bbox = self.draw.textbbox((0, 0), question, font=self.font_md)
        question_width = question_bbox[2] - question_bbox[0]
        question_x = (SCREEN_WIDTH - question_width) // 2
        question_y = face_y + small_face_size + 10
        self.draw.text((question_x, question_y), question, font=self.font_md, fill=COLORS['white'])
        
        # SSH command in purple
        ssh_command = "ssh ovvys@networkii.local"
        ssh_bbox = self.draw.textbbox((0, 0), ssh_command, font=self.font_sm)
        ssh_width = ssh_bbox[2] - ssh_bbox[0]
        ssh_x = (SCREEN_WIDTH - ssh_width) // 2
        ssh_y = question_y + 25
        self.draw.text((ssh_x, ssh_y), ssh_command, font=self.font_sm, fill=COLORS['purple'])
        
        # Networkii command in green
        networkii_command = "run networkii connect"
        networkii_bbox = self.draw.textbbox((0, 0), networkii_command, font=self.font_sm)
        networkii_width = networkii_bbox[2] - networkii_bbox[0]
        networkii_x = (SCREEN_WIDTH - networkii_width) // 2
        networkii_y = ssh_y + 20
        self.draw.text((networkii_x, networkii_y), networkii_command, font=self.font_sm, fill=COLORS['green'])
        
        self.update_display()
    
    def handle_button(self, button_label):
        if button_label == "B":
            # Button B in no internet mode: Reset WiFi
            print("NoInternetScreen: Button B pressed - Reset WiFi") 