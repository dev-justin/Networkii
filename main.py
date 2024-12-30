import time
import argparse
import os
import logging
from pathlib import Path
from src.services.monitor import NetworkMonitor
from src.services.display import Display
from src.services.network_manager import NetworkManager
from src.services.ap_server import APServer
from src.config import TOTAL_SCREENS, DEBOUNCE_TIME, DEFAULT_SCREEN

# Set up logging directory in /var/log
LOG_DIR = '/var/log/networkii'
LOG_FILE = os.path.join(LOG_DIR, 'networkii.log')

# Create log directory with proper permissions
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    os.chmod(LOG_DIR, 0o777)
    # Touch the log file if it doesn't exist and set permissions
    Path(LOG_FILE).touch(exist_ok=True)
    os.chmod(LOG_FILE, 0o666)
except Exception as e:
    print(f"Error setting up log directory: {e}")
    # Fallback to current directory if we can't write to /var/log
    LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    LOG_FILE = os.path.join(LOG_DIR, 'networkii.log')
    os.makedirs(LOG_DIR, exist_ok=True)
    Path(LOG_FILE).touch(exist_ok=True)

# Set up logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('main')

# Add console handler to see logs in terminal
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logging.getLogger('').addHandler(console_handler)

logger.info("Starting Networkii with logging configured to: %s", LOG_FILE)

def run_ap_mode(network_manager, display):
    """Run in AP mode for WiFi configuration"""
    logger.info("Starting AP mode...")
    network_manager.setup_ap_mode()
    display.show_no_connection_screen()
    
    def on_wifi_configured():
        logger.info("WiFi configured successfully, transitioning to monitor mode")
        # Initialize and start monitor mode
        current_screen = DEFAULT_SCREEN
        network_monitor = NetworkMonitor()
        
        def button_handler(pin):
            nonlocal current_screen
            current_time = time.time()
            if current_time - last_button_press < DEBOUNCE_TIME:
                return
            last_button_press = current_time

            if pin == display.disp.BUTTON_B:
                current_screen = max(1, current_screen - 1)
                print(f"Button B pressed - switching to screen {current_screen}")
            elif pin == display.disp.BUTTON_Y:
                current_screen = min(TOTAL_SCREENS, current_screen + 1)
                print(f"Button Y pressed - switching to screen {current_screen}")

        # Register button handler
        display.disp.on_button_pressed(button_handler)
        
        # Main monitoring loop
        while True:
            if not network_manager.check_connection():
                logger.info("Network connection lost, returning to AP mode")
                return run_ap_mode(network_manager, display)
                
            stats = network_monitor.get_stats()
            if current_screen == 1:
                display.show_home_screen(stats)
            elif current_screen == 2:
                display.show_basic_screen(stats)
            else:
                display.show_detailed_screen(stats)
            time.sleep(2)
    
    ap_server = APServer(network_manager, on_wifi_configured)
    ap_server.start()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Networkii - Network Monitor')
    parser.add_argument('--ap-mode', action='store_true', help='Start directly in AP mode')
    args = parser.parse_args()

    logger.info("Networkii starting up...")
    
    # Initialize network manager and display
    network_manager = NetworkManager()
    display = Display()
    last_button_press = 0  # Move this here so it's accessible to both modes
    
    # Start in AP mode if requested or if no connection
    if args.ap_mode or not network_manager.check_connection():
        logger.info("Starting in AP mode ({})", "CLI argument" if args.ap_mode else "No connection")
        print("Starting in AP mode...")
        run_ap_mode(network_manager, display)
        return

    # If we get here, we're starting in monitor mode
    logger.info("Starting in monitor mode")
    run_monitor_mode(network_manager, display)

def run_monitor_mode(network_manager, display):
    """Run the main monitoring interface"""
    logger.info("Starting monitor mode...")
    current_screen = DEFAULT_SCREEN
    network_monitor = NetworkMonitor()
    last_button_press = 0

    def button_handler(pin):
        nonlocal current_screen, last_button_press
        current_time = time.time()
        if current_time - last_button_press < DEBOUNCE_TIME:
            return
        last_button_press = current_time

        if pin == display.disp.BUTTON_B:
            current_screen = max(1, current_screen - 1)
            print(f"Button B pressed - switching to screen {current_screen}")
        elif pin == display.disp.BUTTON_Y:
            current_screen = min(TOTAL_SCREENS, current_screen + 1)
            print(f"Button Y pressed - switching to screen {current_screen}")

    # Register button handler
    display.disp.on_button_pressed(button_handler)
    
    # Main loop to fetch stats and update display
    try:
        while True:
            # Check connection status
            if not network_manager.check_connection():
                logger.info("Network connection lost, switching to AP mode")
                print("Network connection lost. Starting AP mode...")
                run_ap_mode(network_manager, display)
                return
                
            stats = network_monitor.get_stats()
            if current_screen == 1:
                display.show_home_screen(stats)
            elif current_screen == 2:
                display.show_basic_screen(stats)
            else:
                display.show_detailed_screen(stats)
            time.sleep(2)
            
    except KeyboardInterrupt:
        logger.info("Program terminated by user")
        print("\nProgram terminated by user")
    except Exception as e:
        logger.error(f"Error in monitor mode: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
    
