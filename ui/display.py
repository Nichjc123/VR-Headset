# ui/display.py
import tkinter as tk
from PIL import Image, ImageTk
import numpy as np
import cv2
import time
import queue
from threading import Thread

import config
from processing.capture import ScreenCapture
from processing.vr_distortion import VRProcessor
from sensors.reader import SensorReader
from sensors.fusion import SensorFusion

class VRDisplayApp:
    """Main VR display application - orchestrates capture, processing, and rendering"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("VR Display Stream")
        self.config = config
        
        self.screen_width = root.winfo_screenwidth()
        self.screen_height = root.winfo_screenheight()
        
        # Position window on secondary display (assumes it's to the right)
        self.root.geometry(f"{self.screen_width}x{self.screen_height}+{self.screen_width}+0")
        self.root.attributes('-fullscreen', True)
        
        self.canvas = tk.Canvas(
            root,
            width=config.WIDTH,
            height=config.HEIGHT,
            bg='black',
            highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)

        self.running = True
        self.frame_buffer = queue.Queue(maxsize=config.FRAME_BUFFER_SIZE)
        self.render_buffer = queue.Queue(maxsize=config.FRAME_BUFFER_SIZE)
        
        # FPS tracking
        self.last_fps_check = time.time()
        self.frame_count = 0
        self.fps = 0
        
        self.sensor_queue = queue.Queue(maxsize=10)
        
        self.initialize_components()
        self.start_threads()
        self.start_process_sensor_loop()
        self.update_display()
        
        self.root.bind('<Escape>', lambda e: self.quit_app())
    
    def initialize_components(self):
        """Initialize all processing components"""
        self.screen_capture = ScreenCapture(self.config, self.frame_buffer)
        self.vr_processor = VRProcessor(self.config)
        self.sensor_reader = SensorReader(self.config, self.sensor_queue)
        self.sensor_fusion = SensorFusion(self.config, self.sensor_queue)
    
    def start_threads(self):
        """Start capture and render threads"""
        self.screen_capture.start()
        self.sensor_reader.start()
        
        self.render_thread = Thread(target=self.render_frame_thread)
        self.render_thread.daemon = True
        self.render_thread.start()
    
    def start_process_sensor_loop(self):
        """Process sensor data on main thread with timer"""
        self.sensor_fusion.process_sensor_data()
        if self.running:
            self.root.after(2, self.start_process_sensor_loop)

    def render_frame_thread(self):
        """Background thread for VR frame rendering"""
        while self.running:
            # Skip if render buffer is full
            if self.render_buffer.full():
                time.sleep(0.001)
                continue
                
            try:
                if not self.frame_buffer.empty():
                    frame = self.frame_buffer.get_nowait()
                    
                    # Get current orientation with calibration offsets
                    sensor_data = self.sensor_fusion.get_sensor_data()
                    yaw = sensor_data.get("yaw", 0.0) + 100
                    pitch = sensor_data.get("pitch", 0.0) + 12
                    roll = sensor_data.get("roll", 0.0)
                    
                    combined_frame = self.vr_processor.render_frame(frame, yaw, pitch, roll)
                    
                    # Queue management for rendered frames
                    try:
                        self.render_buffer.put_nowait(combined_frame)
                    except queue.Full:
                        try:
                            self.render_buffer.get_nowait()  # Remove oldest
                            self.render_buffer.put_nowait(combined_frame)
                        except queue.Empty:
                            pass
            except queue.Empty:
                time.sleep(0.001)
                continue
            
            time.sleep(0.001)

    def update_display(self):
        """Update UI with rendered VR frames and FPS counter"""
        start_time = time.time()
        
        try:
            if not self.render_buffer.empty():
                combined_frame = self.render_buffer.get_nowait()
                
                image = Image.fromarray(combined_frame)
                photo = ImageTk.PhotoImage(image=image)
                
                self.canvas.delete("all")
                self.canvas.create_image(
                    config.WIDTH//2,
                    config.HEIGHT//2,
                    image=photo,
                    anchor='center'
                )
                # Keep reference to prevent garbage collection
                self.canvas.image = photo
                
                # FPS calculation and display
                self.frame_count += 1
                now = time.time()
                if now - self.last_fps_check >= 1.0:
                    self.fps = self.frame_count / (now - self.last_fps_check)
                    print(f"FPS: {self.fps:.1f}")
                    self.last_fps_check = now
                    self.frame_count = 0
                    
                    self.canvas.create_text(
                        100, 50, 
                        text=f"FPS: {self.fps:.1f}", 
                        fill=config.FPS_TEXT_COLOR, 
                        font=config.FPS_TEXT_FONT
                    )
                
        except queue.Empty:
            pass
        
        # Dynamic scheduling based on render time
        process_time = time.time() - start_time
        next_update = max(1, int(1000/config.RENDER_FPS - process_time * 1000))
        
        if self.running:
            self.root.after(next_update, self.update_display)

    def quit_app(self):
        """Clean shutdown of all components"""
        self.running = False
        self.screen_capture.stop()
        self.sensor_reader.stop()
        self.sensor_fusion.stop()
        self.root.quit()