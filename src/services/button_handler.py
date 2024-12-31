import RPi.GPIO as GPIO
import time
from src.config import TOTAL_SCREENS, DEBOUNCE_TIME
from src.utils.logger import get_logger

logger = get_logger('button_handler')

class ButtonHandler:
    def __init__(self, display, network_manager):
        self.display = display
        self.network_manager = network_manager
        self.current_screen = 1
        self.last_button_press = 0
        self.current_mode = None
        self._handler_registered = False
    
    def _cleanup_gpio(self):
        """Clean up GPIO configuration."""
        logger.debug("Cleaning up GPIO configuration")
        GPIO.setwarnings(False)
        try:
            # Set mode before cleanup
            GPIO.setmode(GPIO.BCM)
            
            # Remove all event detections first
            button_pins = [
                self.display.disp.BUTTON_A,
                self.display.disp.BUTTON_B,
                self.display.disp.BUTTON_X,
                self.display.disp.BUTTON_Y
            ]
            for pin in button_pins:
                try:
                    GPIO.remove_event_detect(pin)
                    logger.debug(f"Removed event detection for pin {pin}")
                except Exception as e:
                    logger.debug(f"No event detection to remove for pin {pin}: {e}")
            
            GPIO.cleanup()
            logger.debug("GPIO cleanup completed")
        except Exception as e:
            logger.warning(f"Error during GPIO cleanup: {e}")
    
    def setup_gpio(self):
        """Initialize GPIO for button handling."""
        logger.debug("Setting up GPIO for button handling")
        try:
            # Clean up first to ensure clean state
            self._cleanup_gpio()
            
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)
            
            # Set up all button pins as inputs with pull-ups
            button_pins = [
                self.display.disp.BUTTON_A,
                self.display.disp.BUTTON_B,
                self.display.disp.BUTTON_X,
                self.display.disp.BUTTON_Y
            ]
            for pin in button_pins:
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
                # Remove any existing event detection before adding new one
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self._universal_button_handler, bouncetime=int(DEBOUNCE_TIME * 1000))
                logger.debug(f"Set up pin {pin} with event detection")
            
            logger.info("GPIO setup completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error setting up GPIO: {e}")
            self._cleanup_gpio()
            return False
    
    def set_mode(self, new_mode):
        """Change the handler mode and update button handlers."""
        if new_mode == self.current_mode:
            logger.debug(f"Already in {new_mode} mode")
            return
        
        logger.info(f"Changing mode from {self.current_mode} to {new_mode}")
        
        # Clean up existing handler
        if self._handler_registered:
            try:
                self.display.disp.on_button_pressed(None)
                logger.debug("Removed existing button handler")
            except Exception as e:
                logger.warning(f"Error removing button handler: {e}")
            self._handler_registered = False
        
        # Clean up GPIO
        self._cleanup_gpio()
        
        # Set up new handler if needed
        if new_mode in ['monitor', 'no_internet']:
            if self.setup_gpio():
                self._handler_registered = True
                logger.info(f"Button handler set up for mode: {new_mode}")
        
        self.current_mode = new_mode
    
    def _universal_button_handler(self, pin):
        """Handle button presses based on current mode."""
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
                    self.network_manager.forget_wifi_connection()
            
            logger.debug(f"Button press on pin {pin} successfully handled")
        except Exception as e:
            logger.error(f"Error handling button press on pin {pin}: {e}", exc_info=True)
    
    def get_current_screen(self):
        """Get the current screen number."""
        return self.current_screen
    
    def cleanup(self):
        """Clean up all handlers and GPIO."""
        logger.info("Cleaning up button handler")
        if self._handler_registered:
            try:
                self.display.disp.on_button_pressed(None)
            except:
                pass
            self._handler_registered = False
        self._cleanup_gpio()
        self.current_mode = None 