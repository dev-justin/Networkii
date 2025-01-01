from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input, Static, Button
from textual.binding import Binding
import logging
import threading
from ..utils.config_manager import config_manager

logger = logging.getLogger('config_server')

class ConfigApp(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #config-container {
        width: 60;
        height: auto;
        border: solid green;
        padding: 1 2;
    }

    .input-label {
        padding-bottom: 1;
    }

    Button {
        margin: 1 0;
    }

    #status {
        height: auto;
        color: $success;
        text-align: center;
    }

    .error {
        color: $error;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "save", "Save Config", show=True),
    ]

    def __init__(self):
        super().__init__()
        self.load_current_config()

    def load_current_config(self):
        """Load the current configuration from config manager"""
        self.config = config_manager.get_config()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Container(id="config-container"):
            yield Static("Ping Target:", classes="input-label")
            yield Input(
                value=self.config.get("ping_target", ""),
                placeholder="e.g. 1.1.1.1",
                id="ping_target"
            )
            yield Static("Speed Test Interval (minutes):", classes="input-label")
            yield Input(
                value=str(self.config.get("speed_test_interval", "")),
                placeholder="5-1440",
                id="speed_test_interval"
            )
            yield Button("Save Configuration", variant="primary")
            yield Static(id="status")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press event."""
        self.save_config()

    def action_save(self) -> None:
        """Handle save keyboard shortcut."""
        self.save_config()

    def save_config(self) -> None:
        """Save the configuration."""
        try:
            ping_target = self.query_one("#ping_target").value
            speed_test_interval = self.query_one("#speed_test_interval").value

            if not ping_target or not speed_test_interval:
                self.show_status("All fields are required", error=True)
                return

            try:
                speed_test_interval = int(speed_test_interval)
                if not (5 <= speed_test_interval <= 1440):
                    raise ValueError("Interval must be between 5 and 1440")
            except ValueError as e:
                self.show_status(str(e), error=True)
                return

            new_config = {
                "ping_target": ping_target,
                "speed_test_interval": speed_test_interval
            }

            config_manager.update_config(new_config)
            self.show_status("Configuration saved successfully!")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            self.show_status(f"Error: {str(e)}", error=True)

    def show_status(self, message: str, error: bool = False) -> None:
        """Show a status message."""
        status = self.query_one("#status")
        status.update(message)
        if error:
            status.add_class("error")
        else:
            status.remove_class("error")

class ConfigServer:
    def __init__(self):
        self.app = ConfigApp()
        self.server_thread = None

    def start(self):
        """Start the Textual app in a background thread"""
        def run_app():
            try:
                logger.info("Starting Textual configuration interface")
                self.app.run()
            except Exception as e:
                logger.error(f"Error starting Textual app: {e}", exc_info=True)
                raise

        self.server_thread = threading.Thread(target=run_app)
        self.server_thread.daemon = True
        self.server_thread.start()

    def stop(self):
        """Stop the Textual app"""
        logger.info("Stopping configuration interface")
        if self.app:
            self.app.exit()
        logger.info("Configuration interface stopped") 