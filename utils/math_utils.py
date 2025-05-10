# utils/math_utils.py
import numpy as np
import math

def create_rotation_matrix(yaw, pitch, roll):
    yaw_rad = math.radians(yaw)
    pitch_rad = math.radians(pitch)
    roll_rad = math.radians(roll)
    
    rot_yaw = np.array([
        [math.cos(yaw_rad), 0, math.sin(yaw_rad)],
        [0, 1, 0],
        [-math.sin(yaw_rad), 0, math.cos(yaw_rad)]
    ])
    
    rot_pitch = np.array([
        [1, 0, 0],
        [0, math.cos(pitch_rad), -math.sin(pitch_rad)],
        [0, math.sin(pitch_rad), math.cos(pitch_rad)]
    ])
    
    rot_roll = np.array([
        [math.cos(roll_rad), -math.sin(roll_rad), 0],
        [math.sin(roll_rad), math.cos(roll_rad), 0],
        [0, 0, 1]
    ])
    
    return rot_yaw @ rot_pitch @ rot_roll