# config.py
WIDTH = 2560
HEIGHT = 1440
CAPTURE_WIDTH = 1280
CAPTURE_HEIGHT = 720

# VR Parameters
IPD = 63.0  # Interpupillary Distance in mm
FOV_DEGREES = 90.0  # Field of View
SCREEN_DISTANCE = 2.0  # Virtual screen distance in meters

# Sensor Configuration
SERIAL_PORT = '/dev/tty.usbserial-0001'
SERIAL_BAUDRATE = 115200
SENSOR_FILTER_ALPHA = 0.05

# Performance Settings
TARGET_FPS = 240
CAPTURE_FPS = 240
RENDER_FPS = 90
FRAME_BUFFER_SIZE = 2
ORIENTATION_THRESHOLD = 0.5  # Degrees

# UI Settings
CURSOR_SIZE = 5
CURSOR_COLOR = (0, 255, 0)
FPS_TEXT_COLOR = "white"
FPS_TEXT_FONT = ("Arial", 24)