import time
import argparse
from src.services.monitor import NetworkMonitor
from src.services.display import Display
from src.services.network_manager import NetworkManager
from src.services.ap_server import APServer
from src.config import TOTAL_SCREENS, DEBOUNCE_TIME, DEFAULT_SCREEN
from src.utils.logger import get_logger

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
    
    def setup_button_handler(self):
        """Set up button handler for screen navigation"""
        def button_handler(pin):
            current_time = time.time()
            if current_time - self.last_button_press < DEBOUNCE_TIME:
                return
            self.last_button_press = current_time

            if pin == self.display.disp.BUTTON_B:
                self.current_screen = max(1, self.current_screen - 1)
                print(f"Button B pressed - switching to screen {self.current_screen}")
            elif pin == self.display.disp.BUTTON_Y:
                self.current_screen = min(TOTAL_SCREENS, self.current_screen + 1)
                print(f"Button Y pressed - switching to screen {self.current_screen}")

        self.display.disp.on_button_pressed(button_handler)
    
    def run_monitor_mode(self):
        """Run the main monitoring interface"""
        logger.info("Starting monitor mode...")
        self.current_screen = DEFAULT_SCREEN
        self.network_monitor = NetworkMonitor()
        self.setup_button_handler()
        
        try:
            while True:
                # Check connection status
                if not self.network_manager.check_connection():
                    logger.info("Network connection lost, switching to AP mode")
                    print("Network connection lost. Starting AP mode...")
                    self.run_ap_mode()
                    return
                    
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
            print("\nProgram terminated by user")
        except Exception as e:
            logger.error(f"Error in monitor mode: {e}")
            print(f"Error: {e}")
    
    def run_ap_mode(self):
        """Run in AP mode for WiFi configuration"""
        logger.info("Starting AP mode...")
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
        
        # Start in AP mode if requested or if no connection
        if ap_mode or not self.network_manager.check_connection():
            logger.info("Starting in AP mode ({})", "CLI argument" if ap_mode else "No connection")
            print("Starting in AP mode...")
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
    
