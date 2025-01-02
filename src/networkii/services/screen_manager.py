class ScreenManager:
    def __init__(self):
        self.screens = {}
        self.current_screen = None
    
    def add_screen(self, name: str, screen):
        """Add a screen to the manager."""
        self.screens[name] = screen
        if self.current_screen is None:
            self.current_screen = name
    
    def switch_screen(self, name: str):
        """Switch to a different screen."""
        if name not in self.screens:
            raise ValueError(f"Screen {name} not found")
        self.current_screen = name
    
    def draw_screen(self, stats):
        """Draw the current screen."""
        if self.current_screen is None:
            return
        self.screens[self.current_screen].draw_screen(stats)
    
    def handle_button(self, button_label: str):
        """Handle button press on current screen."""
        if self.current_screen is None:
            return
        self.screens[self.current_screen].handle_button(button_label)