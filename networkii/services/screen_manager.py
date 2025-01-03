from ..utils.logger import get_logger

logger = get_logger('screen_manager')

class ScreenManager:
    def __init__(self):
        self.screens = {}
        self.current_screen = None
        self.screen_order = ['home', 'basic_stats', 'detailed_stats']  # Define screen navigation order
        
    def add_screen(self, name: str, screen):
        """Add a screen to the manager."""
        self.screens[name] = screen
        screen.set_screen_manager(self)  # Set screen manager reference
        if self.current_screen is None:
            self.current_screen = name
    
    def switch_screen(self, name: str):
        """Switch to a different screen."""
        if name not in self.screens:
            raise ValueError(f"Screen {name} not found")
        self.current_screen = name
    
    def next_screen(self):
        """Switch to the next screen in order."""
        if self.current_screen is None or self.current_screen not in self.screen_order:
            self.current_screen = self.screen_order[0]
            return
            
        current_index = self.screen_order.index(self.current_screen)
        next_index = (current_index + 1) % len(self.screen_order)
        self.current_screen = self.screen_order[next_index]
    
    def previous_screen(self):
        """Switch to the previous screen in order."""
        if self.current_screen is None or self.current_screen not in self.screen_order:
            self.current_screen = self.screen_order[-1]
            return
            
        current_index = self.screen_order.index(self.current_screen)
        prev_index = (current_index - 1) % len(self.screen_order)
        self.current_screen = self.screen_order[prev_index]
    
    def draw_screen(self, stats):
        """Draw the current screen."""
        if self.current_screen is None:
            return
        self.screens[self.current_screen].draw_screen(stats)
    
    def handle_button(self, button_label: str):
        """Handle button press on current screen."""
        if self.current_screen is None:
            return
        
        logger.debug(f"Button {button_label} pressed on {self.current_screen} screen")
        self.screens[self.current_screen].handle_button(button_label)