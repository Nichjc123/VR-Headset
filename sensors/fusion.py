# sensors/fusion.py
import threading
import queue
from processing.filters import LowPassFilter

class SensorFusion:
    """Processes and filters sensor orientation data for VR head tracking"""
    
    def __init__(self, config, sensor_queue):
        self.config = config
        self.sensor_queue = sensor_queue
        self.running = True
        
        # Individual filters for each orientation axis
        self.yaw_filter = LowPassFilter(alpha=config.SENSOR_FILTER_ALPHA)
        self.pitch_filter = LowPassFilter(alpha=config.SENSOR_FILTER_ALPHA)
        self.roll_filter = LowPassFilter(alpha=config.SENSOR_FILTER_ALPHA)
        
        # Thread-safe storage for filtered sensor data
        self.sensor_data = {"yaw": 0.0, "pitch": 0.0, "roll": 0.0}
        self.data_lock = threading.Lock()
    
    def get_sensor_data(self):
        """Return a copy of current sensor data (thread-safe)"""
        with self.data_lock:
            return dict(self.sensor_data)
    
    def process_sensor_data(self):
        """Process all queued sensor data and apply low-pass filtering"""
        try:
            while not self.sensor_queue.empty():
                data = self.sensor_queue.get_nowait()
                
                # Apply low-pass filter to smooth sensor readings
                filtered_yaw = self.yaw_filter.update(data["yaw"])
                filtered_pitch = self.pitch_filter.update(data["pitch"])
                filtered_roll = self.roll_filter.update(data["roll"])
                
                # Update shared data with thread safety
                with self.data_lock:
                    self.sensor_data["yaw"] = filtered_yaw
                    self.sensor_data["pitch"] = filtered_pitch
                    self.sensor_data["roll"] = filtered_roll
                
                self.sensor_queue.task_done()
        except queue.Empty:
            pass
    
    def stop(self):
        """Signal fusion processing to stop"""
        self.running = False