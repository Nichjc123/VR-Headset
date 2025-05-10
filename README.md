# VR Display Prototype System

A prototype VR headset system designed for productivity, providing an immersive extension of your laptop or desktop display. This project explores the fundamental mathematics and graphics processing required for virtual reality technology with a focus on workplace productivity applications.

## Project Overview

This MVP (Minimum Viable Product) demonstrates core VR functionality by creating a stereoscopic display system that extends your computer screen into virtual space. Unlike gaming-focused VR solutions, this system is optimized for productivity tasks such as coding, document editing, and multi-window workflows.

### Key Features

- **Real-time Screen Mirroring**: Captures and displays your desktop in VR
- **Head Tracking**: Uses MPU-9250 sensor for 3DOF (3 Degrees of Freedom) orientation tracking
- **Stereoscopic Rendering**: Creates depth perception through binocular vision
- **Low-latency Processing**: Optimized for responsive interaction
- **Configurable VR Parameters**: Adjustable IPD, FOV, and display settings

### Performance Optimizations

- **JIT Compilation**: Uses Numba for accelerated mathematical computations
- **Multi-threading**: Separate threads for capture, processing, and rendering
- **Frame Buffering**: Manages frame queues to prevent stuttering
- **Caching**: Reuses distortion maps when orientation changes are minimal

### Hardware

- Computer with secondary display output
- MPU-9250 (or compatible) IMU sensor
- Arduino or similar microcontroller running the MPU-9250 library by Hideaki Tai
- The arduino should transmit the data in the following format Yaw: \<value\>, Pitch: \<value\>, Roll: \<value\> (r"Yaw:\s*([-\d.]+),\s*Pitch:\s*([-\d.]+),\s*Roll:\s*([-\d.]+)")


## Software 


### Stereoscopic rendering

Each eye sees a slightly different view, creating depth perception:

1. Apply IPD offset to create two eye positions
2. Calculate perspective projection for each eye
3. Render side-by-side images for VR display

### Sensor Fusion Algorithm

The system uses complementary filtering to combine accelerometer and gyroscope data, reducing noise while maintaining responsiveness.
