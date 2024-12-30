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
        self.current_mode = None  # Can be 'monitor', 'ap', or 'no_internet'
        self.current_button_handler = None
    
    def set_mode(self, new_mode):
        """Change the app mode and update button handlers accordingly."""
        if new_mode == self.current_mode:
            logger.debug(f"Mode already set to {new_mode}, skipping mode change")
            return  # No change needed
        
        logger.info(f"Changing mode from {self.current_mode} to {new_mode}")
        
        # Always clean up existing handler first
        if self.current_button_handler:
            logger.debug("Removing existing button handler")
            try:
                self.display.disp.on_button_pressed(None)
                logger.debug("Successfully removed button handler")
            except Exception as e:
                logger.warning(f"Error removing button handler: {e}")
            self.current_button_handler = None

        # Clean up all GPIO events and configuration
        GPIO.setwarnings(False)  # Disable warnings as we're handling cleanup manually
        try:
            # Remove all event detections first
            button_pins = [self.display.disp.BUTTON_A, self.display.disp.BUTTON_B, 
                          self.display.disp.BUTTON_X, self.display.disp.BUTTON_Y]
            logger.debug(f"Cleaning up event detection for pins: {button_pins}")
            for pin in button_pins:
                try:
                    GPIO.remove_event_detect(pin)
                    logger.debug(f"Successfully removed event detection for pin {pin}")
                except Exception as e:
                    logger.warning(f"Error removing event detection for pin {pin}: {e}")
            
            logger.debug("Performing GPIO cleanup")
            GPIO.cleanup()
            logger.debug("GPIO cleanup completed")
        except Exception as e:
            logger.warning(f"Error during GPIO cleanup: {e}")
        
        # Initialize GPIO for new mode if needed
        if new_mode in ['monitor', 'no_internet']:
            logger.info(f"Setting up GPIO for mode: {new_mode}")
            try:
                # Set up GPIO for button handling
                GPIO.setmode(GPIO.BCM)
                logger.debug("GPIO mode set to BCM")
                
                # Set up all button pins as inputs with pull-ups
                button_pins = [
                    self.display.disp.BUTTON_A,
                    self.display.disp.BUTTON_B,
                    self.display.disp.BUTTON_X,
                    self.display.disp.BUTTON_Y
                ]
                for pin in button_pins:
                    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                    logger.debug(f"Pin {pin} configured as input with pull-up")
                
                # Set up button handler
                self.current_button_handler = self.universal_button_handler
                self.display.disp.on_button_pressed(self.universal_button_handler)
                logger.info(f"Button handler successfully set up for mode: {new_mode}")
            except Exception as e:
                logger.error(f"Error setting up button handler: {e}", exc_info=True)
                self.current_button_handler = None
                try:
                    logger.debug("Attempting cleanup after button handler setup failure")
                    for pin in button_pins:
                        try:
                            GPIO.remove_event_detect(pin)
                            logger.debug(f"Cleaned up event detection for pin {pin}")
                        except Exception as cleanup_error:
                            logger.warning(f"Error cleaning up pin {pin}: {cleanup_error}")
                    GPIO.cleanup()
                    logger.debug("Emergency GPIO cleanup completed")
                except Exception as cleanup_error:
                    logger.error(f"Error during emergency cleanup: {cleanup_error}")
        
        self.current_mode = new_mode
        logger.info(f"Mode successfully changed to: {new_mode}")

    def universal_button_handler(self, pin):
        """Single callback that knows how to behave based on the current app state/screen."""
        current_time = time.time()
        if current_time - self.last_button_press < DEBOUNCE_TIME:
            logger.debug(f"Button press on pin {pin} debounced (last press: {self.last_button_press:.2f}s ago)")
            return
        
        self.last_button_press = current_time
        logger.debug(f"Button press detected on pin {pin} in mode: {self.current_mode}")

        try:
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
                    logger.info("Button B pressed - initiating WiFi reset")
                    self.reset_wifi_and_enter_ap()
            
            logger.debug(f"Button press on pin {pin} successfully handled")
        except Exception as e:
            logger.error(f"Error handling button press on pin {pin}: {e}", exc_info=True)

    def reset_wifi_and_enter_ap(self):
        """Reset WiFi credentials and enter AP mode"""
        logger.info("Resetting WiFi credentials and entering AP mode")
        self.set_mode('ap')  # This will clean up handlers
        self.network_manager.forget_wifi_connection()
        self.run_ap_mode()

    def run_monitor_mode(self):
        """Run the main monitoring interface"""
        logger.info("Starting monitor mode...")
        self.current_screen = DEFAULT_SCREEN
        self.network_monitor = NetworkMonitor()
        self.set_mode('monitor')
        
        # Track if we're in internet mode or no-internet mode
        in_internet_mode = True
        
        try:
            while True:
                # First check if we have WiFi connection
                if not self.network_manager.has_wifi_connection():
                    logger.info("No WiFi connection, switching to AP mode")
                    self.set_mode('ap')
                    self.run_ap_mode()
                    return
                
                # Then check if we have internet
                has_internet = self.network_manager.check_connection()
                
                # Handle mode transitions only when status changes
                if has_internet and not in_internet_mode:
                    logger.info("Internet connection restored")
                    self.set_mode('monitor')
                    in_internet_mode = True
                elif not has_internet and in_internet_mode:
                    logger.info("Internet connection lost")
                    self.set_mode('no_internet')
                    in_internet_mode = False
                
                # Show appropriate screen based on internet status
                # Don't change modes here since we already handled transitions above
                if not has_internet:
                    logger.info("WiFi connected but no internet, showing no internet screen")
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
            self.set_mode(None)  # Clean up handlers

    def run_ap_mode(self):
        """Run in AP mode for WiFi configuration"""
        logger.info("Starting AP mode...")
        self.set_mode('ap')
        self.network_manager.setup_ap_mode()
        self.display.show_no_connection_screen()
        
        def on_wifi_configured():
            logger.info("WiFi configured successfully, transitioning to monitor mode")
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
    
