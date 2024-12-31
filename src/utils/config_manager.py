import os
import json
import logging

logger = logging.getLogger('config_manager')

class ConfigManager:
    DEFAULT_CONFIG = {
        'ping_target': '1.1.1.1'
    }
    
    def __init__(self):
        self.config_dir = '/etc/networkii'
        self.config_file = os.path.join(self.config_dir, 'config.json')
        self.config = self.DEFAULT_CONFIG.copy()
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
                    logger.debug(f"Loaded configuration: {self.config}")
            else:
                # Save default config if no file exists
                self.save_config()
                logger.debug("Created default configuration file")
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
    
    def get_ping_target(self):
        """Get the configured ping target"""
        return self.config.get('ping_target', self.DEFAULT_CONFIG['ping_target'])

# Create a singleton instance
config_manager = ConfigManager() 