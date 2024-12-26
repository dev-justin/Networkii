import json
import os
import time
from threading import Lock

# Path to store the config file
CONFIG_FILE = 'network_settings.json'

# Default configuration
DEFAULT_CONFIG = {
    # Network testing configurations
    'speedtest_interval': 300,  # How often to run speed test (in seconds)
    'ping_interval': 1,         # How often to check ping/packet loss (in seconds)
    'display_refresh': 1,       # How often to update the display (in seconds)
    'ping_count': 10,          # Number of pings to send for averaging
    'ping_target': '8.8.8.8',  # Target IP/domain for ping tests
    'ping_timeout': 1,         # Timeout for each ping (in seconds)

    # Quality thresholds
    'ping_excellent': 20,      # ms
    'ping_good': 50,          # ms
    'ping_fair': 100,         # ms
    'jitter_excellent': 5,    # ms
    'jitter_good': 15,        # ms
    'jitter_fair': 25,        # ms
    'loss_excellent': 0.5,    # %
    'loss_good': 2.0,        # %
    'loss_fair': 5.0,        # %

    # Display configurations
    'display_rotation': 180,    # Display rotation in degrees
    'display_width': 320,      # Display width in pixels
    'display_height': 240,     # Display height in pixels

    # Graph configurations
    'graph_duration': 300,     # Duration to show on graph (in seconds)
    'graph_max_ping': 100,     # Maximum ping value for graph scaling (ms)
}

# Add after the DEFAULT_CONFIG
INITIALIZATION_KEYS = {
    'graph_duration',  # Keys that require reinitialization
    'ping_count',
    'display_width',
    'display_height',
    'display_rotation'
}

class Config:
    def __init__(self):
        self.lock = Lock()
        self.last_read_time = 0
        self.callbacks = {}  # Store callbacks for specific keys
        self.load_config()

    def load_config(self):
        """Load configuration from file or create with defaults"""
        with self.lock:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    stored_config = json.load(f)
                    # Update default config with stored values
                    self.config = DEFAULT_CONFIG.copy()
                    self.config.update(stored_config)
            else:
                self.config = DEFAULT_CONFIG.copy()
                self.save_config()
            self.last_read_time = os.path.getmtime(CONFIG_FILE) if os.path.exists(CONFIG_FILE) else 0

    def save_config(self):
        """Save current configuration to file"""
        try:
            print("Starting to save config...")
            # Check file permissions
            directory = os.path.dirname(CONFIG_FILE) or '.'
            if os.path.exists(CONFIG_FILE):
                print(f"File exists, permissions: {oct(os.stat(CONFIG_FILE).st_mode)[-3:]}")
            else:
                print(f"File doesn't exist, directory permissions: {oct(os.stat(directory).st_mode)[-3:]}")
            
            with open(CONFIG_FILE, 'w') as f:
                print("File opened for writing...")
                json.dump(self.config, f, indent=4)
                print("JSON dumped to file...")
            
            self.last_read_time = os.path.getmtime(CONFIG_FILE)
            print(f"Successfully saved config to {CONFIG_FILE}")
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Effective user ID: {os.geteuid() if hasattr(os, 'geteuid') else 'N/A'}")
            raise

    def check_for_updates(self):
        """Check if config file has been modified"""
        if os.path.exists(CONFIG_FILE):
            current_mtime = os.path.getmtime(CONFIG_FILE)
            if current_mtime > self.last_read_time:
                print("Config file changed, reloading...")  # Debug
                old_config = self.config.copy()
                self.load_config()
                # Check which values changed and call callbacks
                for key in self.config:
                    if key in old_config and old_config[key] != self.config[key]:
                        print(f"Value changed for {key}: {old_config[key]} -> {self.config[key]}")  # Debug
                        if key in self.callbacks:
                            try:
                                for callback in self.callbacks[key]:
                                    print(f"Running callback for {key}")  # Debug
                                    callback(self.config[key])
                                print(f"Callbacks completed for {key}")  # Debug
                            except Exception as e:
                                print(f"Error in callback for {key}: {e}")  # Don't let callback errors stop us
                return True
            return False

    def get(self, key):
        """Get a configuration value"""
        with self.lock:
            return self.config.get(key)

    def update(self, updates):
        """Update configuration with new values"""
        print(f"Updating config with: {updates}")
        with self.lock:
            try:
                print("Acquired lock, updating config dict...")
                self.config.update(updates)
                print("Config dict updated, saving to file...")
                self.save_config()
                # After saving, notify about changes
                self._notify_changes(updates)
                print("Save completed")
            except Exception as e:
                print(f"Error in update method: {e}")
                raise

    def _notify_changes(self, updates):
        """Notify callbacks of changes"""
        try:
            for key, new_value in updates.items():
                if key in self.callbacks:
                    print(f"Notifying callbacks for {key}")
                    for callback in self.callbacks[key]:
                        try:
                            callback(new_value)
                        except Exception as e:
                            print(f"Error in callback for {key}: {e}")
        except Exception as e:
            print(f"Error in notify_changes: {e}")

    def register_callback(self, key, callback):
        """Register a callback for when a specific key changes"""
        with self.lock:
            if key not in self.callbacks:
                self.callbacks[key] = []
            self.callbacks[key].append(callback)

# Create a global config instance
config = Config()

# Constants that shouldn't be configurable via web interface
TITLE_FONT_SIZE = 20
TEXT_FONT_SIZE = 16

COLOR_BACKGROUND = 'black'
COLOR_TITLE = 'white'
COLOR_SPEED = 'green'
COLOR_PING = 'yellow'
COLOR_LOSS = 'red'
COLOR_EXCELLENT = 'lime'
COLOR_GOOD = 'green'
COLOR_FAIR = 'yellow'
COLOR_POOR = 'red'
GRAPH_COLOR = 'blue'
GRAPH_GRID_COLOR = 'darkgray'

FACE_EXCELLENT = '(◕‿◕)'
FACE_GOOD = '(◠‿◠)'
FACE_FAIR = '(•︵•)'
FACE_POOR = '(╥﹏╥)'

# Helper function to get config values
def get(key):
    return config.get(key) 