from abc import ABC, abstractmethod
from PIL import Image, ImageDraw
from ..models.network_stats import NetworkStats
from ..config import SCREEN_WIDTH, SCREEN_HEIGHT

class BaseScreen(ABC):
    def __init__(self, display):
        """Initialize with display instance for access to shared resources."""
        self.display = display
        self.draw = display.draw
        self.image = display.image
        self.disp = display.disp
        
        # Quick access to fonts
        self.font_xs = display.font_xs
        self.font_sm = display.font_sm
        self.font_md = display.font_md
        self.font_lg = display.font_lg
        self.font_xl = display.font_xl
        
        # Quick access to images
        self.face_images = display.face_images
        self.heart_image = display.heart_image
    
    @abstractmethod
    def draw_screen(self, stats: NetworkStats):
        """Draw the screen content."""
        pass
    
    def handle_button(self, button_label: str):
        """Handle button press events. Override in screens that need button interaction."""
        pass
    
    def clear_screen(self):
        """Clear the screen with black background."""
        self.draw.rectangle((0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), fill=(0, 0, 0))
    
    def update_display(self):
        """Update the physical display."""
        self.disp.st7789.set_window()
        self.disp.st7789.display(self.image)