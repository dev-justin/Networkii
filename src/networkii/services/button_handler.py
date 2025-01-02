import RPi.GPIO as GPIO
import time
from networkii.config import TOTAL_SCREENS, DEBOUNCE_TIME
from networkii.utils.logger import get_logger

logger = get_logger('button_handler')

class ButtonHandler:
    def __init__(self, display):    
        self.display = display
        self.current_screen = 1
        self.last_button_press = 0
        self.current_mode = None
        self._handler_registered = False
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)  # Set mode at initialization
    
    def _cleanup_gpio(self):
        """Clean up GPIO configuration."""
        try:
            # Ensure mode is set before any operations
            GPIO.setmode(GPIO.BCM)
            
            # Remove all event detections first
            if hasattr(self.display, 'disp'):
                button_pins = [
                    self.display.disp.BUTTON_A,
                    self.display.disp.BUTTON_B,
                    self.display.disp.BUTTON_X,
                    self.display.disp.BUTTON_Y
                ]
                for pin in button_pins:
                    try:
                        GPIO.remove_event_detect(pin)
                    except Exception as e:
                        logger.debug(f"No event detection to remove for pin {pin}: {e}")
            
            # Clean up PWM and GPIO
            try:
                GPIO.cleanup()
                # Reset mode after cleanup for next operations
                GPIO.setmode(GPIO.BCM)
            except Exception as e:
                logger.debug(f"GPIO cleanup error: {e}")
                
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
            # Ensure mode is set even after errors
            GPIO.setmode(GPIO.BCM)
    
    def setup_gpio(self):
        """Initialize GPIO for button handling."""
        try:
            # Clean up first to ensure clean state
            self._cleanup_gpio()
            
            # Mode is already set in cleanup, but set warnings again
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
                try:
                    GPIO.remove_event_detect(pin)
                except:
                    pass
                GPIO.add_event_detect(pin, GPIO.FALLING, callback=self._universal_button_handler, bouncetime=int(DEBOUNCE_TIME * 1000))
            
            logger.debug("GPIO setup completed")
            return True
        except Exception as e:
            logger.error(f"Error setting up GPIO: {e}")
            self._cleanup_gpio()
            return False
    
    def set_button_config(self, new_mode):
        """Change the handler mode and update button handlers."""
        if new_mode == self.current_mode:
            return
        
        logger.debug(f"Changing button mode from {self.current_mode} to {new_mode}")
        
        # Clean up existing handler
        if self._handler_registered:
            try:
                self.display.disp.on_button_pressed(None)
            except Exception as e:
                logger.error(f"Error removing button handler: {e}")
            self._handler_registered = False
        
        # Clean up GPIO
        self._cleanup_gpio()
        
        # Set up new handler if needed
        if new_mode in ['monitor', 'no_internet']:
            if self.setup_gpio():
                self._handler_registered = True
                logger.debug(f"Button handler set up for mode: {new_mode}")
        
        self.current_mode = new_mode
    
    def _universal_button_handler(self, pin):
        """Handle button presses based on current mode."""
        current_time = time.time()
        if current_time - self.last_button_press < DEBOUNCE_TIME:
            return
        
        self.last_button_press = current_time
        
        try:
            if self.current_mode == 'monitor':
                # Handle monitor mode navigation
                if pin == self.display.disp.BUTTON_B:
                    self.current_screen = max(1, self.current_screen - 1)
                    logger.debug(f"Button B pressed - switching to screen {self.current_screen}")
                elif pin == self.display.disp.BUTTON_Y:
                    self.current_screen = min(TOTAL_SCREENS, self.current_screen + 1)
                    logger.debug(f"Button Y pressed - switching to screen {self.current_screen}")
            
        except Exception as e:
            logger.error(f"Error handling button press on pin {pin}: {e}", exc_info=True)
    
    def get_current_screen(self):
        """Get the current screen number."""
        return self.current_screen
    
    def cleanup(self):
        """Clean up all handlers and GPIO."""
        logger.debug("Cleaning up button handler")
        if self._handler_registered:
            try:
                if hasattr(self.display, 'disp'):
                    self.display.disp.on_button_pressed(None)
            except:
                pass
            self._handler_registered = False
        self._cleanup_gpio()
        self.current_mode = None 