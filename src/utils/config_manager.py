import os
import json
from src.config import USER_DEFAULTS
from src.utils.logger import get_logger

# Get logger for this module
logger = get_logger('config_manager')

class ConfigManager:
    def __init__(self):
        logger.info("Initializing ConfigManager...")
        # Use ovvys's home directory for configuration
        self.config_file = '/home/ovvys/Networkii/config.json'
        logger.info(f"Using config file: {self.config_file}")
        self.config = USER_DEFAULTS.copy()
        logger.info(f"Starting with defaults: {self.config}")
        self.load_config()
    
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
                # Save default config if no file exists
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
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def get_config(self):
        """Get the entire configuration"""
        return self.config.copy()
    
    def update_config(self, new_config):
        """Update configuration with new values"""
        self.config.update(new_config)
        self.save_config()
        logger.info(f"Configuration updated: {self.config}")
    
    def get_setting(self, key):
        """Get a configuration setting by key, falling back to default if not found"""
        value = self.config.get(key, USER_DEFAULTS.get(key))
        return value

# Create a singleton instance
config_manager = ConfigManager() 