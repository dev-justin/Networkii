# Display settings
TOTAL_SCREENS = 3
DEFAULT_SCREEN = 1
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Network settings
DEFAULT_TARGET_HOST = "1.1.1.1"
DEFAULT_HISTORY_LENGTH = 300
DEFAULT_SPEED_TEST_INTERVAL = 30  # minutes

# Button settings
DEBOUNCE_TIME = 0.3  # seconds

# Asset sizes and spacing
FACE_SIZE = 128
HEART_SIZE = 28
HEART_SPACING = 10
HEART_GAP = 8

# Network states
NETWORK_STATES = {
    'excellent': {
        'message': "Network is Purring!",
        'face': 'assets/faces/excellent.png',
        'threshold': 90
    },
    'good': {
        'message': "All Systems Go!",
        'face': 'assets/faces/good.png',
        'threshold': 70
    },
    'fair': {
        'message': "Hanging in There!",
        'face': 'assets/faces/fair.png',
        'threshold': 60
    },
    'poor': {
        'message': "Having Hiccups... ",
        'face': 'assets/faces/poor.png',
        'threshold': 50
    },
    'critical': {
        'message': "Help, I'm Sick!",
        'face': 'assets/faces/critical.png',
        'threshold': 0
    }
} 