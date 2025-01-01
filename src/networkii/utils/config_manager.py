import os
import json
import time
from pathlib import Path
from networkii.config import USER_DEFAULTS
from networkii.utils.logger import get_logger

# Get logger for this module
logger = get_logger('config_manager')

class ConfigManager:

    CONFIG_DIR = Path.home() / '.networkii'
    CONFIG_FILE = CONFIG_DIR / 'config.json'
    CONFIG_TIMESTAMP_FILE = CONFIG_DIR / '.config_updated'

    def __init__(self):
        logger.info("============ Initializing ConfigManager =============")
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        self.config_file = str(self.CONFIG_FILE)
        self.timestamp_file = str(self.CONFIG_TIMESTAMP_FILE)
        self.last_check_time = 0
        self.config = USER_DEFAULTS.copy()  # Initialize with defaults first
        logger.info(f"Using config file: {self.config_file}")
        self.load_config()  # Then load from file if it exists
    
    def _update_timestamp(self):
        """Update the timestamp file to signal config changes"""
        try:
            Path(self.timestamp_file).touch()
        except Exception as e:
            logger.error(f"Error updating timestamp file: {e}")

    def _check_for_updates(self):
        """Check if config has been modified by another process"""
        try:
            if os.path.exists(self.timestamp_file):
                mtime = os.path.getmtime(self.timestamp_file)
                if mtime > self.last_check_time:
                    logger.debug("Config change detected, reloading from file")
                    self.load_config()
                    self.last_check_time = mtime
        except Exception as e:
            logger.error(f"Error checking for updates: {e}")
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                logger.info(f"Reading config from: {self.config_file}")
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values while preserving defaults
                    self.config.update(loaded_config)
                    logger.info(f"Loaded configuration: {self.config}")
            else:
                logger.info(f"No config file found at {self.config_file}, creating with defaults")
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            logger.info(f"Saving config to: {self.config_file}")
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                logger.info("Configuration saved successfully")
            self._update_timestamp()  # Signal that config has changed
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_config(self):
        """Get the entire configuration"""
        self._check_for_updates()  # Check for changes before returning
        return self.config.copy()
    
    def update_config(self, new_config):
        """Update configuration with new values"""
        self.config.update(new_config)
        self.save_config()
        logger.info(f"Configuration updated: {self.config}")
    
    def get_setting(self, key):
        """Get a configuration setting by key, falling back to default if not found"""
        self._check_for_updates()  # Check for changes before returning
        return self.config.get(key, USER_DEFAULTS.get(key))

# Create a singleton instance
config_manager = ConfigManager() 