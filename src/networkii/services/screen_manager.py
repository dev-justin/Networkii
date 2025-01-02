class ScreenManager:
    def __init__(self):
        self.screens = {}
        self.current_screen_name = None

    def add_screen(self, name, screen):
        """Register a screen object by a string name."""
        self.screens[name] = screen

    def switch_screen(self, name):
        """Set the active screen by name."""
        if name in self.screens:
            self.current_screen_name = name
            print(f"Switched to screen: {name}")
        else:
            print(f"Screen {name} not found!")

    def handle_button(self, button_label):
        """Dispatch button press events to the active screen."""
        if self.current_screen_name is None:
            return
        current_screen = self.screens[self.current_screen_name]
        # If the current screen has its own handle_button method, call it
        if hasattr(current_screen, 'handle_button'):
            current_screen.handle_button(button_label)

    def draw(self, stats):
        """Ask the active screen to draw/update its view, if it exists."""
        if self.current_screen_name is None:
            return
        current_screen = self.screens[self.current_screen_name]
        # Assuming each screen has a draw(stats) method
        if hasattr(current_screen, 'draw'):
            current_screen.draw(stats)