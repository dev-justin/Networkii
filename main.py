import time
from src.services.monitor import NetworkMonitor
from src.services.display import Display
from src.services.network_manager import NetworkManager
from src.services.ap_server import APServer
from src.config import TOTAL_SCREENS, DEBOUNCE_TIME, DEFAULT_SCREEN

def run_ap_mode(network_manager, display):
    """Run in AP mode for WiFi configuration"""
    network_manager.setup_ap_mode()
    display.show_no_connection_screen()
    ap_server = APServer(network_manager)
    ap_server.start()

def main():
    # Initialize network manager and display
    network_manager = NetworkManager()
    display = Display()
    
    # Check network connection
    if not network_manager.check_connection():
        print("No network connection. Starting AP mode...")
        run_ap_mode(network_manager, display)
        return

    # Network is connected, run main app
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
        print("\nProgram terminated by user")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
    
