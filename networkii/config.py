# User configurable defaults
# These values can be changed through the web interface
USER_DEFAULTS = {
    'ping_target': '1.1.1.1',
    'speed_test_interval': 30  # minutes
}

# Display settings
TOTAL_SCREENS = 4  # Now includes: Home, Basic Stats, Basic, and Detailed
DEFAULT_SCREEN = 1
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240

# Network settings
DEFAULT_HISTORY_LENGTH = 300
RECENT_HISTORY_LENGTH = 20  # Number of samples for health calculation

# Button settings
DEBOUNCE_TIME = 0.3  # seconds

# Font sizes
FONT_XS = 10   # Extra small for tiny details
FONT_SM = 14   # Small for medium-priority info
FONT_MD = 16   # Medium for standard text
FONT_LG = 24   # Large for important labels
FONT_XL = 36   # Extra large for primary metrics

# Display metrics
METRIC_WIDTH = 18
METRIC_SPACING = 5
METRIC_RIGHT_MARGIN = 0
METRIC_TOP_MARGIN = 10
METRIC_BOTTOM_MARGIN = 10
BAR_WIDTH = 8
BAR_SPACING = 5
BAR_START_X = 0

# Asset sizes and spacing
FACE_SIZE = 128
HEART_SIZE = 28
HEART_SPACING = 10
HEART_GAP = 8

# Colors
COLORS = {
    'green': (0, 255, 127),
    'red': (255, 99, 71),
    'purple': (147, 112, 219),
    'gray': (80, 80, 80),
    'white': (255, 255, 255),
}

# Network metric thresholds
METRIC_THRESHOLDS = {
    'ping': {
        'excellent': 20,
        'good': 30,
        'fair': 60,
        'poor': 100,
        'weight': 0.4
    },
    'jitter': {
        'excellent': 2,
        'good': 5,
        'fair': 10,
        'poor': 20,
        'weight': 0.4
    },
    'packet_loss': {
        'excellent': 0,
        'good': 0.1,
        'fair': 0.5,
        'poor': 1,
        'weight': 0.2
    }
}

# Health status thresholds
HEALTH_THRESHOLDS = {
    'excellent': {
        'message': "Network is Purring!",
        'face': 'assets/faces/excellent.png',
        'threshold': 90,
        'hearts': 5
    },
    'good': {
        'message': "All Systems Go!",
        'face': 'assets/faces/good.png',
        'threshold': 70,
        'hearts': 4
    },
    'fair': {
        'message': "Hanging in There!",
        'face': 'assets/faces/fair.png',
        'threshold': 60,
        'hearts': 3
    },
    'poor': {
        'message': "Having Hiccups... ",
        'face': 'assets/faces/poor.png',
        'threshold': 50,
        'hearts': 2
    },
    'critical': {
        'message': "Help, I'm Sick!",
        'face': 'assets/faces/critical.png',
        'threshold': 0,
        'hearts': 1
    }
} 