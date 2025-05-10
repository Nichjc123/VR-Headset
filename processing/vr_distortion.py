# processing/vr_distortion.py
import numpy as np
import cv2
import math
from numba import jit
from utils.math_utils import create_rotation_matrix

@jit(nopython=True)
def compute_vr_distortion(x_flat, y_flat, z_flat, half_ipd, focal_length, target_width, target_height, 
                          rot_matrix, img_height, img_width):
    """Compute distortion maps for VR rendering using JIT compilation for performance"""
    size = len(x_flat)
    left_rotated_x = np.zeros(size)
    left_rotated_y = np.zeros(size)
    left_rotated_z = np.zeros(size)
    
    # Left eye transformation with IPD offset
    for i in range(size):
        x_with_ipd = x_flat[i] - half_ipd
        left_rotated_x[i] = x_with_ipd * rot_matrix[0, 0] + y_flat[i] * rot_matrix[0, 1] + z_flat[i] * rot_matrix[0, 2]
        left_rotated_y[i] = x_with_ipd * rot_matrix[1, 0] + y_flat[i] * rot_matrix[1, 1] + z_flat[i] * rot_matrix[1, 2]
        left_rotated_z[i] = x_with_ipd * rot_matrix[2, 0] + y_flat[i] * rot_matrix[2, 1] + z_flat[i] * rot_matrix[2, 2]
    
    left_screen_x = np.full(size, -1.0)
    left_screen_y = np.full(size, -1.0)
    
    # Project points to screen coordinates (perspective projection)
    for i in range(size):
        if left_rotated_z[i] > 0:
            left_screen_x[i] = (left_rotated_x[i] / left_rotated_z[i] * focal_length) + target_width / 2
            left_screen_y[i] = (left_rotated_y[i] / left_rotated_z[i] * focal_length) + target_height / 2
    
    left_map_x = left_screen_x.reshape(img_height, img_width)
    left_map_y = left_screen_y.reshape(img_height, img_width)
    
    right_rotated_x = np.zeros(size)
    right_rotated_y = np.zeros(size)
    right_rotated_z = np.zeros(size)
    
    # Right eye transformation with opposite IPD offset
    for i in range(size):
        x_with_ipd = x_flat[i] + half_ipd
        right_rotated_x[i] = x_with_ipd * rot_matrix[0, 0] + y_flat[i] * rot_matrix[0, 1] + z_flat[i] * rot_matrix[0, 2]
        right_rotated_y[i] = x_with_ipd * rot_matrix[1, 0] + y_flat[i] * rot_matrix[1, 1] + z_flat[i] * rot_matrix[1, 2]
        right_rotated_z[i] = x_with_ipd * rot_matrix[2, 0] + y_flat[i] * rot_matrix[2, 1] + z_flat[i] * rot_matrix[2, 2]
    
    right_screen_x = np.full(size, -1.0)
    right_screen_y = np.full(size, -1.0)
    
    for i in range(size):
        if right_rotated_z[i] > 0:
            right_screen_x[i] = (right_rotated_x[i] / right_rotated_z[i] * focal_length) + target_width / 2
            right_screen_y[i] = (right_rotated_y[i] / right_rotated_z[i] * focal_length) + target_height / 2
    
    right_map_x = right_screen_x.reshape(img_height, img_width)
    right_map_y = right_screen_y.reshape(img_height, img_width)
    
    return left_map_x, left_map_y, right_map_x, right_map_y

class VRProcessor:
    def __init__(self, config):
        self.config = config
        self.precompute_vr_parameters()
        self.map_cache = {}
        self.last_orientation = None
        
    def precompute_vr_parameters(self):
        """Pre-compute fixed VR parameters for performance"""
        self.target_width = self.config.CAPTURE_WIDTH // 2
        self.target_height = self.config.CAPTURE_HEIGHT
        
        self.fov_rad = math.radians(self.config.FOV_DEGREES)
        self.focal_length = (self.target_width / 2) / math.tan(self.fov_rad / 2)
        
        # Convert IPD from mm to pixels
        self.half_ipd = self.config.IPD * self.focal_length / (self.config.SCREEN_DISTANCE * 1000) / 2
        
        # Create coordinate grids for distortion mapping
        y_grid, x_grid = np.mgrid[0:self.target_height, 0:self.target_width]
        self.x_centered = x_grid - self.target_width / 2
        self.y_centered = y_grid - self.target_height / 2
        self.z_values = np.ones_like(x_grid) * self.focal_length
        
        # Flatten for vectorized operations
        self.x_flat = self.x_centered.flatten()
        self.y_flat = self.y_centered.flatten()
        self.z_flat = self.z_values.flatten()
    
    def should_use_cache(self, current_orientation):
        if self.last_orientation is None:
            return False
        diff = np.abs(np.array(current_orientation) - np.array(self.last_orientation))
        return np.all(diff < self.config.ORIENTATION_THRESHOLD)
    
    def compute_distortion_maps(self, yaw, pitch, roll):
        current_orientation = (yaw, pitch, roll)
        
        # Use cached maps if orientation hasn't changed significantly
        if self.should_use_cache(current_orientation) and self.map_cache:
            return self.map_cache
        
        rotation_matrix = create_rotation_matrix(yaw, pitch, roll)
        
        try:
            maps = compute_vr_distortion(
                self.x_flat, self.y_flat, self.z_flat, 
                self.half_ipd, self.focal_length, 
                self.target_width, self.target_height,
                rotation_matrix, 
                self.target_height, self.target_width
            )
        except Exception as e:
            print(f"Error in distortion calculation: {e}")
            # Fallback to non-JIT version if JIT compilation fails
            maps = self.compute_vr_distortion_fallback(yaw, pitch, roll)
        
        self.map_cache = maps
        self.last_orientation = current_orientation
        return maps
    
    def compute_vr_distortion_fallback(self, yaw, pitch, roll):
        """Non-JIT fallback implementation for compatibility"""
        rotation_matrix = create_rotation_matrix(yaw, pitch, roll)
        
        # Left eye
        left_coords = np.zeros((len(self.x_flat), 3))
        left_coords[:, 0] = self.x_flat - self.half_ipd
        left_coords[:, 1] = self.y_flat
        left_coords[:, 2] = self.z_flat
        
        left_rotated = left_coords @ rotation_matrix.T
        
        valid_indices = left_rotated[:, 2] > 0
        left_screen_x = np.full(left_rotated.shape[0], -1.0)
        left_screen_y = np.full(left_rotated.shape[0], -1.0)
        
        left_screen_x[valid_indices] = (left_rotated[valid_indices, 0] / left_rotated[valid_indices, 2] * self.focal_length) + self.target_width / 2
        left_screen_y[valid_indices] = (left_rotated[valid_indices, 1] / left_rotated[valid_indices, 2] * self.focal_length) + self.target_height / 2
        
        left_map_x = left_screen_x.reshape(self.target_height, self.target_width)
        left_map_y = left_screen_y.reshape(self.target_height, self.target_width)
        
        # Right eye
        right_coords = np.zeros((len(self.x_flat), 3))
        right_coords[:, 0] = self.x_flat + self.half_ipd
        right_coords[:, 1] = self.y_flat
        right_coords[:, 2] = self.z_flat
        
        right_rotated = right_coords @ rotation_matrix.T
        
        valid_indices = right_rotated[:, 2] > 0
        right_screen_x = np.full(right_rotated.shape[0], -1.0)
        right_screen_y = np.full(right_rotated.shape[0], -1.0)
        
        right_screen_x[valid_indices] = (right_rotated[valid_indices, 0] / right_rotated[valid_indices, 2] * self.focal_length) + self.target_width / 2
        right_screen_y[valid_indices] = (right_rotated[valid_indices, 1] / right_rotated[valid_indices, 2] * self.focal_length) + self.target_height / 2
        
        right_map_x = right_screen_x.reshape(self.target_height, self.target_width)
        right_map_y = right_screen_y.reshape(self.target_height, self.target_width)
        
        return left_map_x, left_map_y, right_map_x, right_map_y
    
    def render_frame(self, frame, yaw, pitch, roll):
        """Render a frame with VR distortion for both eyes"""
        left_map_x, left_map_y, right_map_x, right_map_y = self.compute_distortion_maps(yaw, pitch, roll)
        
        # Apply distortion maps using OpenCV's remap
        left_eye = cv2.remap(frame, left_map_x.astype(np.float32), left_map_y.astype(np.float32), 
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        
        right_eye = cv2.remap(frame, right_map_x.astype(np.float32), right_map_y.astype(np.float32), 
                            cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        
        # Combine eyes side by side
        combined_frame = np.hstack((left_eye, right_eye))
        
        # Resize to target display resolution if needed
        if combined_frame.shape[1] != self.config.WIDTH or combined_frame.shape[0] != self.config.HEIGHT//2:
            combined_frame = cv2.resize(combined_frame, (self.config.WIDTH, self.config.HEIGHT//2))
        
        return combined_frame