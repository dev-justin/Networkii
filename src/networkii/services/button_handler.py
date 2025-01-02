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
        
        # Initialize GPIO once
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        
        # Define button actions for each mode
        self.mode_actions = {
            'monitor': {
                self.display.disp.BUTTON_A: self._monitor_button_a,
                self.display.disp.BUTTON_B: self._monitor_button_b,
                self.display.disp.BUTTON_X: self._monitor_button_x,
                self.display.disp.BUTTON_Y: self._monitor_button_y,
            },
            'no_internet': {
                self.display.disp.BUTTON_A: self._no_internet_button_a,
                self.display.disp.BUTTON_B: self._no_internet_button_b,
                self.display.disp.BUTTON_X: self._no_internet_button_x,
                self.display.disp.BUTTON_Y: self._no_internet_button_y,
            },
            'setup': {
                self.display.disp.BUTTON_A: self._setup_button_a,
                self.display.disp.BUTTON_B: self._setup_button_b,
                self.display.disp.BUTTON_X: self._setup_button_x,
                self.display.disp.BUTTON_Y: self._setup_button_y,
            }
        }
        
        # Set up GPIO once
        self.setup_gpio()
    
    # Button handlers for monitor mode
    def _monitor_button_a(self):
        """Button A in monitor mode: Toggle auto-scroll"""
        logger.debug("Monitor mode: Button A pressed - Toggle auto-scroll")
        # Implement auto-scroll toggle
    
    def _monitor_button_b(self):
        """Button B in monitor mode: Previous screen"""
        self.current_screen = max(1, self.current_screen - 1)
        logger.debug(f"Monitor mode: Button B pressed - Previous screen {self.current_screen}")
    
    def _monitor_button_x(self):
        """Button X in monitor mode: Refresh stats"""
        logger.debug("Monitor mode: Button X pressed - Refresh stats")
        # Implement stats refresh
    
    def _monitor_button_y(self):
        """Button Y in monitor mode: Next screen"""
        self.current_screen = min(TOTAL_SCREENS, self.current_screen + 1)
        logger.debug(f"Monitor mode: Button Y pressed - Next screen {self.current_screen}")
    
    # Button handlers for no internet mode
    def _no_internet_button_a(self):
        """Button A in no internet mode: Start AP"""
        logger.debug("No Internet mode: Button A pressed - Start AP")
        # Implement AP start
    
    def _no_internet_button_b(self):
        """Button B in no internet mode: Reset WiFi"""
        logger.debug("No Internet mode: Button B pressed - Reset WiFi")
        # Implement WiFi reset
    
    def _no_internet_button_x(self):
        """Button X in no internet mode: Show help"""
        logger.debug("No Internet mode: Button X pressed - Show help")
        # Implement help display
    
    def _no_internet_button_y(self):
        """Button Y in no internet mode: Retry connection"""
        logger.debug("No Internet mode: Button Y pressed - Retry connection")
        # Implement connection retry
    
    # Button handlers for setup mode
    def _setup_button_a(self):
        """Button A in setup mode: Confirm"""
        logger.debug("Setup mode: Button A pressed - Confirm")
        # Implement setup confirmation
    
    def _setup_button_b(self):
        """Button B in setup mode: Cancel"""
        logger.debug("Setup mode: Button B pressed - Cancel")
        # Implement setup cancellation
    
    def _setup_button_x(self):
        """Button X in setup mode: Previous option"""
        logger.debug("Setup mode: Button X pressed - Previous option")
        # Implement previous option
    
    def _setup_button_y(self):
        """Button Y in setup mode: Next option"""
        logger.debug("Setup mode: Button Y pressed - Next option")
        # Implement next option
    
    def _universal_button_handler(self, pin):
        """Universal button handler that dispatches to the appropriate mode handler"""
        current_time = time.time()
        if current_time - self.last_button_press < DEBOUNCE_TIME:
            return
        
        self.last_button_press = current_time
        
        try:
            # Look up the handler for current mode and pin
            if self.current_mode in self.mode_actions:
                handler = self.mode_actions[self.current_mode].get(pin)
                if handler:
                    handler()
                else:
                    logger.debug(f"No handler for pin {pin} in mode {self.current_mode}")
            else:
                logger.debug(f"No handlers registered for mode {self.current_mode}")
                
        except Exception as e:
            logger.error(f"Error handling button press on pin {pin}: {e}", exc_info=True)
    
    def setup_gpio(self):
        """Initialize GPIO for button handling."""
        try:
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
                GPIO.add_event_detect(pin, GPIO.FALLING, 
                                    callback=self._universal_button_handler, 
                                    bouncetime=int(DEBOUNCE_TIME * 1000))
            
            logger.debug("GPIO setup completed")
            return True
        except Exception as e:
            logger.error(f"Error setting up GPIO: {e}")
            return False
    
    def set_button_config(self, new_mode):
        """Change the handler mode."""
        if new_mode == self.current_mode:
            return
        
        logger.debug(f"Changing button mode from {self.current_mode} to {new_mode}")
        self.current_mode = new_mode
    
    def get_current_screen(self):
        """Get the current screen number."""
        return self.current_screen
    
    def cleanup(self):
        """Clean up GPIO."""
        logger.debug("Cleaning up button handler")
        try:
            GPIO.cleanup()
        except Exception as e:
            logger.error(f"Error during GPIO cleanup: {e}")
        self.current_mode = None 