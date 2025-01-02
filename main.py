import time
import argparse
import threading
from networkii.services.network_monitor import NetworkMonitor
from networkii.services.display import Display
from networkii.services.button_handler import ButtonHandler
from networkii.utils.logger import get_logger
from networkii.utils.network import check_connection, has_wifi_saved, start_ap

logger = get_logger('main')
logger.info("============ Starting Networkii =============")

class NetworkiiApp:
    def __init__(self):
        self.display = Display()
        self.button_handler = ButtonHandler(self.display)
        self.network_monitor = None
        self.button_config = None 
        self.monitor_thread = None
        self.monitor_running = False
        self.latest_stats = None
    
    def set_button_config(self, new_config):
        """Change the app mode and update handlers."""
        if new_config == self.button_config:
            return
        
        logger.debug(f"Changing mode from {self.button_config} to {new_config}")
        self.button_handler.set_button_config(new_config)
        self.button_config = new_config

    def network_monitor_loop(self):
        """Background thread for network monitoring"""
        logger.debug("Network monitor thread started")
        while self.monitor_running:
            try:
                self.latest_stats = self.network_monitor.get_stats()
                time.sleep(2)  # Get new stats every 2 seconds
            except Exception as e:
                logger.error(f"Error in monitor thread: {e}")
                time.sleep(1)  # Wait before retrying on error

    def run_monitor_mode(self):
        """Run the main monitoring interface"""
        logger.info("Starting monitor mode")
        self.network_monitor = NetworkMonitor()
        self.set_button_config('monitor')
        
        # Start monitor thread
        self.monitor_running = True
        self.monitor_thread = threading.Thread(target=self.network_monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        # Track if we're in internet mode or no-internet mode
        in_internet_mode = True
        
        try:
            while True:
                # First check if we have WiFi connection
                if not has_wifi_saved('wlan0'):
                    logger.info("No WiFi connection, switching to setup mode")
                    self.set_button_config(None)
                    self.monitor_running = False
                    if self.monitor_thread:
                        self.monitor_thread.join()
                    self.no_wifi_mode()
                    return
                
                # Check if we have internet on preferred interface
                has_internet = check_connection('wlan0') or check_connection('usb0')
                
                # Handle mode transitions only when status changes
                if has_internet and not in_internet_mode:
                    logger.info("Internet connection restored")
                    self.set_button_config('monitor')
                    in_internet_mode = True
                elif not has_internet and in_internet_mode:
                    logger.info("Internet connection lost")
                    self.set_button_config(None)
                    in_internet_mode = False
                
                # Show appropriate screen based on internet status
                if not has_internet:
                    logger.debug("WiFi connected but no internet, showing no internet screen")
                    self.display.show_no_internet_screen()
                elif self.latest_stats:  # Only update if we have stats
                    current_screen = self.button_handler.get_current_screen()
                    if current_screen == 1:
                        self.display.show_home_screen(self.latest_stats)
                    elif current_screen == 2:
                        self.display.show_basic_stats_screen(self.latest_stats)
                    elif current_screen == 3:
                        self.display.show_basic_screen(self.latest_stats)
                    else:
                        self.display.show_detailed_screen(self.latest_stats)
                
                time.sleep(0.1)  # Update display every 100ms
                
        except KeyboardInterrupt:
            logger.info("Program terminated by user")
        except Exception as e:
            logger.error(f"Error in monitor mode: {e}")
        finally:
            self.monitor_running = False
            if self.monitor_thread:
                self.monitor_thread.join()
            self.set_button_config(None)  # Clean up handlers

    def no_wifi_mode(self):
        """ No WiFi mode - show no connection screen """
        logger.info("No WiFi connection, starting AP and showing setup screen")
        self.set_button_config(None)
        start_ap()
        self.display.setup_screen()
    
    def run(self, setup_mode=False):
        """Main entry point for the application"""

        logger.debug("Networkii starting up...")
        
        try:
            if setup_mode or not has_wifi_saved('wlan0'):
                self.no_wifi_mode()
            else:
                self.run_monitor_mode()
        finally:
            self.monitor_running = False
            if self.monitor_thread:
                self.monitor_thread.join()
            self.button_handler.cleanup()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Networkii - Network Monitor')
    parser.add_argument('--setup-mode', action='store_true', help='Start directly in setup mode')
    args = parser.parse_args()

    # Create and run the application
    app = NetworkiiApp()
    app.run(setup_mode=args.setup_mode)

if __name__ == "__main__":
    main()
    
