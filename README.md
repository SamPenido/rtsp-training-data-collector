# RTSP Frame Capture for AI Training

This project contains a Python script that connects to an RTSP camera stream and captures frames at adjustable intervals. The captured frames are saved as JPEG images with configurable quality, making it ideal for collecting large datasets for computer vision experiments and AI training.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Execution](#execution)
- [Code Explanation](#code-explanation)
  - [Environment and RTSP Connection](#environment-and-rtsp-connection)
  - [Round Management](#round-management)
  - [Frame Capture and Saving](#frame-capture-and-saving)
  - [Metadata Logging](#metadata-logging)
- [Output File: `test_summary.log`](#output-file-test_summarylog)
- [Customization](#customization)
- [License](#license)

## Overview
This Python script connects to an RTSP camera stream, captures frames at user-defined intervals, and saves them as JPEG images. It is designed to maximize data collection for later use in AI training and computer vision tasks. Parameters such as capture intervals, JPEG quality, and connection details can be easily adjusted.

## Features
- **Adjustable Capture Intervals:** Modify the time between frame captures.
- **Adjustable JPEG Quality:** Configure the quality of saved JPEG images.
- **Configurable Connection:** Easily adjust the RTSP connection parameters (username, password, IP, port, and stream path) via an environment file.
- **Round-Based Data Management:** Automatically manages rounds of data capture with unique frame naming.
- **Metadata Logging:** Detailed session logs are appended to `test_summary.log`, including timing, capture parameters, and storage statistics.

## Requirements
- Python 3.x
- [OpenCV](https://opencv.org/) (`cv2`)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- Standard Python libraries: `os`, `re`, `time`, `shutil`, `datetime`

## Configuration
1. **Install Dependencies:**
   ```bash
   pip install opencv-python python-dotenv
   ```

2. **Create a .env File:**
   In the project root, create a file named `.env` with the following variables:
   ```
   CAMERA_USERNAME=your_username
   CAMERA_PASSWORD=your_password
   CAMERA_IP=your_camera_ip
   CAMERA_PORT=your_camera_port
   RTSP_STREAM_PATH=/path/to/stream
   ```
   Update these values to match your camera's settings.

## Execution
Run the script using:
```bash
python frame_collector.py
```

The script will:
- Connect to the RTSP stream.
- Capture frames at the configured interval (default is one frame every 2 seconds).
- Save the frames in the `rtsp_test_frames` directory.
- Log session metadata to `test_summary.log`.

## Code Explanation

### Environment and RTSP Connection
- **Environment Variables:**
  The script uses dotenv to load camera credentials and stream parameters from the `.env` file.
- **RTSP URL Construction:**
  It constructs the RTSP URL and masks sensitive information (e.g., the password) in console outputs.

### Round Management
- **Round ID Determination:**
  The function `get_next_round_id()` determines the next round ID by:
  - Reading the current round from `test_round_state.txt`.
  - Scanning the image directory for existing rounds if the state file is missing or contains invalid data.
- **State Update:**
  After the capture session, the current round ID is saved back to `test_round_state.txt` for use in future runs.

### Frame Capture and Saving
- **Connection to RTSP Stream:**
  The script utilizes OpenCV's `cv2.VideoCapture` to connect to the RTSP stream.
- **Capture Loop:**
  It continuously reads frames for a configured duration (default is 1440 minutes or 24 hours). Frames are saved only if the defined interval (default 2 seconds) has elapsed.
- **Saving Frames:**
  Each frame is saved as a JPEG image using a filename format:
  ```
  round_<round_id>_<frame_number>_<timestamp>.jpg
  ```
  The JPEG quality is adjustable via the script parameters.

### Metadata Logging
- **Statistics Calculation:**
  After capturing, the script calculates the total number of frames saved, total storage size, and average size per frame.
- **Log File:**
  Metadata including start and end times, configured duration versus actual duration, capture interval, JPEG quality, and storage statistics is appended to `test_summary.log`.

## Output File: `test_summary.log`
The `test_summary.log` file consolidates detailed session metadata, including:
- **Session Timings:** Start and end times.
- **Duration:** Configured test duration versus the actual runtime.
- **Capture Parameters:** Capture interval and JPEG quality.
- **Statistics:** Number of frames saved, total data size, and average size per frame.

This log is critical for analyzing the performance of each capture session and making adjustments for future runs.

## Customization
The script allows you to easily modify key parameters:
- **Capture Interval:** Change the time between frame captures.
- **JPEG Quality:** Adjust the quality setting for JPEG image saving.
- **RTSP Connection Parameters:** Update the `.env` file to modify connection details.
- **Test Duration:** Set the overall runtime of the capture session.

## License
MIT License
