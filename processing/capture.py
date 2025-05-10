# processing/capture.py
import numpy as np
import cv2
import time
import queue
import mss
import Quartz
from threading import Thread

class ScreenCapture:
    """Handles screen capture and cursor overlay for VR display"""
    
    def __init__(self, config, frame_buffer):
        self.config = config
        self.frame_buffer = frame_buffer
        self.running = True
        self.screen_width = None
        self.screen_height = None
        self.initialize_screen_dimensions()
    
    def initialize_screen_dimensions(self):
        """Get primary monitor dimensions using mss"""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            self.screen_width = monitor["width"]
            self.screen_height = monitor["height"]
    
    def get_mouse_position(self):
        """Get current mouse cursor position using Quartz (macOS)"""
        mouse_loc = Quartz.CGEventGetLocation(Quartz.CGEventCreate(None))
        return int(mouse_loc.x), int(mouse_loc.y)
    
    def overlay_cursor(self, frame, x, y):
        """Draw cursor on frame, scaled to capture resolution"""
        # Scale cursor position from screen resolution to capture resolution
        x = int(x * (self.config.CAPTURE_WIDTH / self.screen_width))
        y = int(y * (self.config.CAPTURE_HEIGHT / self.screen_height))
        cv2.circle(frame, (x, y), self.config.CURSOR_SIZE, self.config.CURSOR_COLOR, -1)
        return frame
    
    def capture_screen(self):
        """Main capture loop - grabs screen, processes, and queues frames"""
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Primary monitor
            
            capture_region = {
                "left": 0,
                "top": 0,
                "width": self.screen_width,
                "height": self.screen_height
            }
            
            while self.running:
                start_time = time.time()
                
                # Capture screen
                img = sct.grab(capture_region)
                frame = np.array(img)
                
                # Downscale for performance
                frame = cv2.resize(frame, (self.config.CAPTURE_WIDTH, self.config.CAPTURE_HEIGHT))
                
                # Convert BGRA to RGB for display
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2RGB)
                
                # Add cursor overlay
                mouse_x, mouse_y = self.get_mouse_position()
                frame = self.overlay_cursor(frame, mouse_x, mouse_y)
                
                # Queue management - replace oldest frame if buffer is full
                try:
                    self.frame_buffer.put_nowait(frame)
                except queue.Full:
                    try:
                        self.frame_buffer.get_nowait()  # Remove oldest
                        self.frame_buffer.put_nowait(frame)  # Add new
                    except queue.Empty:
                        pass
                
                # Maintain target FPS
                frame_duration = time.time() - start_time
                target_sleep = max(0, 1/self.config.CAPTURE_FPS - frame_duration)
                time.sleep(target_sleep)
    
    def start(self):
        """Start capture thread"""
        self.capture_thread = Thread(target=self.capture_screen)
        self.capture_thread.daemon = True
        self.capture_thread.start()
        return self.capture_thread
    
    def stop(self):
        """Stop capture thread"""
        self.running = False