import os
import json
import logging
from ..config import USER_DEFAULTS

logger = logging.getLogger('config_manager')

class ConfigManager:
    def __init__(self):
        logger.info("Initializing ConfigManager...")
        # Use ~/.config/networkii for configuration
        self.config_dir = os.path.expanduser('~/.config/networkii')
        self.config_file = os.path.join(self.config_dir, 'config.json')
        logger.info(f"Using config file: {self.config_file}")
        self.config = USER_DEFAULTS.copy()
        logger.info(f"Starting with defaults: {self.config}")
        print(f"Starting with defaults: {self.config}")
        self.load_config()
    
    def load_config(self):
        """Load configuration from file"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update config with loaded values while preserving defaults
                    self.config.update(loaded_config)
                    logger.info(f"Loaded configuration from {self.config_file}: {self.config}")
            else:
                # Save default config if no file exists
                self.save_config()
                logger.info(f"Created default configuration at {self.config_file}")
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
            
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
                logger.debug("Configuration saved successfully")
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
        print(f"Getting setting: {key}, {self.config.get(key)}")
        return self.config.get(key, USER_DEFAULTS.get(key))

# Create a singleton instance
config_manager = ConfigManager() 