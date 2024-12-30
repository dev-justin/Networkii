from src.services.display import Display

def main():
    # Initialize the display
    display = Display()
    
    # Show the no connection screen
    display.show_no_connection_screen()
    
    print("Showing no connection screen. Press Ctrl+C to exit.")
    
    # Keep the script running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("\nExiting...")

if __name__ == "__main__":
    main() 