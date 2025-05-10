# sensors/reader.py
import serial
import time
import re
import queue
from threading import Thread

class SensorReader:
    """Reads orientation data from MPU sensor via serial connection"""
    
    def __init__(self, config, sensor_queue):
        self.config = config
        self.sensor_queue = sensor_queue
        self.running = True
        # Regex pattern to extract yaw, pitch, roll values from serial data
        self.pattern = r"Yaw:\s*([-\d.]+),\s*Pitch:\s*([-\d.]+),\s*Roll:\s*([-\d.]+)"
    
    def sensor_reader(self):
        """Main sensor reading loop - parses serial data and queues sensor values"""
        try:
            ser = serial.Serial(self.config.SERIAL_PORT, self.config.SERIAL_BAUDRATE, timeout=1)
            # Clear any existing data in buffers
            ser.reset_input_buffer()
            ser.reset_output_buffer()
            
            time.sleep(2)  # Allow serial connection to stabilize
            print("Serial connection established, waiting for sensor data...")
            
            while self.running:
                if ser.in_waiting > 0:
                    raw_line = ser.readline()
                    
                    if raw_line:
                        line = raw_line.decode('utf-8', errors='replace').strip()
                        match = re.search(self.pattern, line)
                        
                        if match:
                            # Extract orientation values
                            yaw = float(match.group(1))
                            pitch = float(match.group(2))
                            roll = float(match.group(3))
                            
                            # Queue sensor data with timestamp
                            try:
                                self.sensor_queue.put_nowait({
                                    "yaw": yaw,
                                    "pitch": pitch,
                                    "roll": roll,
                                    "timestamp": time.time()
                                })
                            except queue.Full:
                                # Skip if queue is full to prevent blocking
                                pass
                
                time.sleep(0.001)  # Prevent CPU overload
        
        except Exception as e:
            print(f"Error in sensor reading thread: {e}")
        finally:
            # Ensure serial connection is properly closed
            if 'ser' in locals() and ser.is_open:
                ser.close()
                print("Serial connection closed")
    
    def start(self):
        """Start sensor reading thread"""
        self.sensor_thread = Thread(target=self.sensor_reader)
        self.sensor_thread.daemon = True
        self.sensor_thread.start()
        return self.sensor_thread
    
    def stop(self):
        """Signal sensor reading to stop"""
        self.running = False