import time
import argparse
from src.services.monitor import NetworkMonitor
from src.services.display import Display
from src.services.network_manager import NetworkManager
from src.services.ap_server import APServer
from src.config import TOTAL_SCREENS, DEBOUNCE_TIME, DEFAULT_SCREEN
from src.utils.logger import get_logger
import RPi.GPIO as GPIO

# Get logger for main module
logger = get_logger('main')
logger.info("Starting Networkii")

class NetworkiiApp:
    def __init__(self):
        self.network_manager = NetworkManager()
        self.display = Display()
        self.current_screen = DEFAULT_SCREEN
        self.last_button_press = 0
        self.network_monitor = None
        self.current_mode = 'monitor'  # Can be 'monitor', 'ap', or 'no_internet'
        self.current_button_handler = None
    
    def setup_button_handler(self):
        """Set up the universal button handler"""
        try:
            # Remove existing handler if any
            if self.current_button_handler:
                self.display.disp.on_button_pressed(None)
                # Clean up GPIO events for all buttons
                for pin in [self.display.disp.BUTTON_A, self.display.disp.BUTTON_B, 
                          self.display.disp.BUTTON_X, self.display.disp.BUTTON_Y]:
                    try:
                        GPIO.remove_event_detect(pin)
                    except:
                        pass  # Ignore if event detection wasn't set
            
            # Set new handler
            self.current_button_handler = self.universal_button_handler
            self.display.disp.on_button_pressed(self.universal_button_handler)
        except Exception as e:
            logger.error(f"Error setting button handler: {e}")
            self.current_button_handler = None

    def universal_button_handler(self, pin):
        """Single callback that knows how to behave based on the current app state/screen."""
        current_time = time.time()
        if current_time - self.last_button_press < DEBOUNCE_TIME:
            return
        self.last_button_press = current_time

        if self.current_mode == 'monitor':
            # Handle monitor mode navigation
            if pin == self.display.disp.BUTTON_B:
                self.current_screen = max(1, self.current_screen - 1)
                logger.info(f"Button B pressed - switching to screen {self.current_screen}")
            elif pin == self.display.disp.BUTTON_Y:
                self.current_screen = min(TOTAL_SCREENS, self.current_screen + 1)
                logger.info(f"Button Y pressed - switching to screen {self.current_screen}")
        
        elif self.current_mode == 'no_internet':
            # Handle no internet screen (reset WiFi)
            if pin == self.display.disp.BUTTON_B:
                logger.info("Button B pressed - resetting WiFi configuration")
                self.reset_wifi_and_enter_ap()
        
        # AP mode has no button handlers

    def reset_wifi_and_enter_ap(self):
        """Reset WiFi credentials and enter AP mode"""
        logger.info("Resetting WiFi credentials and entering AP mode")
        self.display.disp.on_button_pressed(None)  # Clear button handler
        self.current_button_handler = None
        self.network_manager.forget_wifi_connection()
        self.run_ap_mode()

    def run_monitor_mode(self):
        """Run the main monitoring interface"""
        logger.info("Starting monitor mode...")
        self.current_screen = DEFAULT_SCREEN
        self.current_mode = 'monitor'
        self.network_monitor = NetworkMonitor()
        
        # Track if we're in internet mode or no-internet mode
        in_internet_mode = True
        self.setup_button_handler()  # Set up initial button handler
        
        try:
            while True:
                # First check if we have WiFi connection
                if not self.network_manager.has_wifi_connection():
                    logger.info("No WiFi connection, switching to AP mode")
                    self.current_mode = 'ap'
                    self.display.disp.on_button_pressed(None)  # Clear button handler
                    self.current_button_handler = None
                    self.run_ap_mode()
                    return
                
                # Then check if we have internet
                has_internet = self.network_manager.check_connection()
                
                # Handle mode transitions
                if has_internet and not in_internet_mode:
                    logger.info("Internet connection restored")
                    self.current_mode = 'monitor'
                    self.setup_button_handler()
                    in_internet_mode = True
                elif not has_internet and in_internet_mode:
                    logger.info("Internet connection lost")
                    self.current_mode = 'no_internet'
                    self.setup_button_handler()
                    in_internet_mode = False
                
                # Show appropriate screen based on internet status
                if not has_internet:
                    logger.info("WiFi connected but no internet, showing no internet screen")
                    self.current_mode = 'no_internet'
                    self.setup_button_handler()
                    self.display.show_no_internet_screen()
                else:
                    stats = self.network_monitor.get_stats()
                    if self.current_screen == 1:
                        self.display.show_home_screen(stats)
                    elif self.current_screen == 2:
                        self.display.show_basic_screen(stats)
                    else:
                        self.display.show_detailed_screen(stats)
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            logger.info("Program terminated by user")
        except Exception as e:
            logger.error(f"Error in monitor mode: {e}")
            # Clean up handler on error
            self.display.set_button_handler(None)

    def run_ap_mode(self):
        """Run in AP mode for WiFi configuration"""
        logger.info("Starting AP mode...")
        self.current_mode = 'ap'
        self.network_manager.setup_ap_mode()
        self.display.show_no_connection_screen()
        
        def on_wifi_configured():
            logger.info("WiFi configured successfully, transitioning to monitor mode")
            self.current_mode = 'monitor'
            self.run_monitor_mode()
        
        ap_server = APServer(self.network_manager, on_wifi_configured)
        ap_server.start()
    
    def run(self, ap_mode=False):
        """Main entry point for the application"""
        logger.info("Networkii starting up...")
        
        # Start in AP mode if requested or if no WiFi connection
        if ap_mode or not self.network_manager.has_wifi_connection():
            logger.info("Starting in AP mode ({})", "CLI argument" if ap_mode else "No WiFi connection")
            self.run_ap_mode()
        else:
            # If we get here, we're starting in monitor mode
            logger.info("Starting in monitor mode")
            self.run_monitor_mode()

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
    
