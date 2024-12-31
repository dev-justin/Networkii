import time
import argparse
from src.services.monitor import NetworkMonitor
from src.services.display import Display
from src.services.network_manager import NetworkManager
from src.services.ap_server import APServer
from src.services.button_handler import ButtonHandler
from src.utils.logger import get_logger

# Get logger for main module
logger = get_logger('main')
logger.info("Starting Networkii")

class NetworkiiApp:
    def __init__(self):
        self.network_manager = NetworkManager()
        self.display = Display()
        self.network_monitor = None
        self.button_config = None  # Can be 'monitor', 'ap', or 'no_internet'
        self.button_handler = ButtonHandler(self.display, self.network_manager)
    
    def set_button_config(self, new_config):
        """Change the app mode and update handlers."""
        if new_config == self.button_config:
            return
        
        logger.info(f"Changing mode from {self.button_config} to {new_config}")
        self.button_handler.set_button_config(new_config)
        self.button_config = new_config

    def run_monitor_mode(self):
        """Run the main monitoring interface"""
        logger.info("Starting monitor mode...")
        self.network_monitor = NetworkMonitor()
        self.set_button_config('monitor')
        
        # Track if we're in internet mode or no-internet mode
        in_internet_mode = True
        
        try:
            while True:
                # First check if we have WiFi connection
                if not self.network_manager.has_wifi_connection():
                    logger.info("No WiFi connection, switching to AP mode")
                    self.set_button_config('ap')
                    self.run_ap_mode()
                    return
                
                # Check if we have internet on preferred interface (wlan0 or usb0)
                has_internet = self.network_manager.check_connection()
                
                # Handle mode transitions only when status changes
                if has_internet and not in_internet_mode:
                    logger.info("Internet connection restored")
                    self.set_button_config('monitor')
                    in_internet_mode = True
                elif not has_internet and in_internet_mode:
                    logger.info("Internet connection lost")
                    self.set_button_config('no_internet')
                    in_internet_mode = False
                
                # Show appropriate screen based on internet status
                if not has_internet:
                    logger.info("WiFi connected but no internet, showing no internet screen")
                    self.display.show_no_internet_screen()
                else:
                    stats = self.network_monitor.get_stats()
                    current_screen = self.button_handler.get_current_screen()
                    if current_screen == 1:
                        self.display.show_home_screen(stats)
                    elif current_screen == 2:
                        self.display.show_basic_screen(stats)
                    else:
                        self.display.show_detailed_screen(stats)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            logger.info("Program terminated by user")
        except Exception as e:
            logger.error(f"Error in monitor mode: {e}")
        finally:
            self.set_button_config(None)  # Clean up handlers

    def run_ap_mode(self):
        """Run in AP mode for WiFi configuration"""
        logger.info("Starting AP mode...")
        self.set_button_config('ap')
        self.display.show_no_connection_screen()
        self.network_manager.setup_ap_mode()
        
        def on_wifi_configured():
            logger.info("WiFi configured successfully, transitioning to monitor mode")
            self.run_monitor_mode()
        
        ap_server = APServer(self.network_manager, on_wifi_configured)
        ap_server.start()
    
    def run(self, ap_mode=False):
        """Main entry point for the application"""
        logger.info("Networkii starting up...")
        
        try:
            # Start in AP mode if requested or if no WiFi connection
            if ap_mode or not self.network_manager.has_wifi_connection():
                logger.info("Booting into AP mode (%s)", "CLI argument" if ap_mode else "No WiFi connection")
                self.run_ap_mode()
            else:
                logger.info("Booting into monitor mode")
                self.run_monitor_mode()
        finally:
            self.button_handler.cleanup()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Networkii - Network Monitor')
    parser.add_argument('--ap-mode', action='store_true', help='Start directly in AP mode')
    args = parser.parse_args()

    # Create and run the application
    app = NetworkiiApp()
    app.run(ap_mode=args.ap_mode)

if __name__ == "__main__":
    main()
    
