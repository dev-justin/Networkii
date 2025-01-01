import os
import json
import logging
from ..config import USER_DEFAULTS
from ..utils.logger import init_logging

# Initialize logging first
init_logging()
logger = logging.getLogger('config_manager')

class ConfigManager:
    def __init__(self):
        logger.info("Initializing ConfigManager...")
        # Use project directory for configuration
        self.config_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.config_file = os.path.join(self.config_dir, 'config.json')
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
        logger.info(f"Getting setting: {key}, value: {value}")
        return value

# Create a singleton instance
config_manager = ConfigManager() 