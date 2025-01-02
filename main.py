import time
import argparse
import threading
from networkii.services.network_monitor import NetworkMonitor
from networkii.services.display import Display
from networkii.services.screen_manager import ScreenManager
from networkii.screens import HomeScreen, SetupScreen, NoInternetScreen, BasicStatsScreen, DetailedStatsScreen
from networkii.utils.logger import get_logger
from networkii.utils.network import check_connection, has_wifi_saved, start_ap
import RPi.GPIO as GPIO

logger = get_logger('main')
logger.info("============ Starting Networkii =============")

class NetworkiiApp:
    def __init__(self):
        self.display = Display()
        self.screen_manager = ScreenManager()
        
        # Initialize all screens
        self.screen_manager.add_screen('home', HomeScreen(self.display))
        self.screen_manager.add_screen('setup', SetupScreen(self.display))
        self.screen_manager.add_screen('no_internet', NoInternetScreen(self.display))
        self.screen_manager.add_screen('basic_stats', BasicStatsScreen(self.display))
        self.screen_manager.add_screen('detailed_stats', DetailedStatsScreen(self.display))
        
        # Setup button handlers
        display_hat = self.display.disp
        display_hat.on_button_pressed(self.button_pressed_callback)
        
        self.network_monitor = None
        self.monitor_thread = None
        self.monitor_running = False
        self.latest_stats = None
        self.current_mode = None
    
    def button_pressed_callback(self, pin):
        """
        Single callback for any button press on Display HAT Mini.
        We'll just figure out which button (A/B/X/Y) was pressed and
        then delegate to the ScreenManager, which in turn calls the
        current screen’s handle_button().
        """
        # Confirm it's actually pressed, not released
        if not self.display_hat.read_button(pin):
            return

        button_label = self.button_map.get(pin)
        if button_label is None:
            logger.warning(f"Unknown button pin {pin}")
            return

        logger.debug(f"[{self.current_mode}] Button {button_label} pressed")

        # Delegate all button logic to the ScreenManager, which will
        # call handle_button() on the *active* screen.
        self.screen_manager.handle_button(button_label)

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
        self.current_mode = 'monitor'
        
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
                    self.current_mode = None
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
                    self.current_mode = 'monitor'
                    in_internet_mode = True
                    self.screen_manager.switch_screen('home')  # Return to home screen when internet is restored
                elif not has_internet and in_internet_mode:
                    logger.info("Internet connection lost")
                    self.current_mode = 'no_internet'
                    in_internet_mode = False
                    self.screen_manager.switch_screen('no_internet')  # Show no internet screen
                
                # Update current screen with latest stats
                if not has_internet:
                    self.screen_manager.draw_screen(None)  # No stats needed for no internet screen
                elif self.latest_stats:
                    self.screen_manager.draw_screen(self.latest_stats)  # Update current screen with latest stats
                
                time.sleep(0.1)  # Update display every 100ms
                
        except KeyboardInterrupt:
            logger.info("Program terminated by user")
        except Exception as e:
            logger.error(f"Error in monitor mode: {e}")
        finally:
            self.monitor_running = False
            if self.monitor_thread:
                self.monitor_thread.join()
            self.current_mode = None

    def no_wifi_mode(self):
        """ No WiFi mode - show no connection screen """
        logger.info("No WiFi connection, starting AP and showing setup screen")
        
        # Clean up existing mode first
        self.monitor_running = False
        if self.monitor_thread:
            self.monitor_thread.join()
        
        # Start AP mode and show setup screen
        start_ap()
        self.current_mode = 'no_internet'
        self.screen_manager.switch_screen('setup')
        self.screen_manager.draw(None)
    
    def run(self, setup_mode=False):
        """Main entry point for the application"""
        logger.debug("Networkii starting up...")
        
        try:
            if setup_mode or not has_wifi_saved('wlan0'):
                self.no_wifi_mode()
            else:
                self.run_monitor_mode()
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
        finally:
            # Ensure proper cleanup
            self.monitor_running = False
            if self.monitor_thread:
                self.monitor_thread.join()
            GPIO.cleanup()  # Final GPIO cleanup

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
    
