# RTSP Frame Capture and Classification for AI Training

This project contains tools for connecting to RTSP camera streams to capture frames for computer vision and AI training. It includes a frame capture utility and a manual classification tool to organize datasets for machine learning.

## Table of Contents
- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Configuration](#configuration)
- [Frame Capture](#frame-capture)
  - [Execution](#execution)
  - [Code Explanation](#code-explanation)
    - [Environment and RTSP Connection](#environment-and-rtsp-connection)
    - [Round Management](#round-management)
    - [Frame Capture and Saving](#frame-capture-and-saving)
    - [Metadata Logging](#metadata-logging)
  - [Output File: `test_summary.log`](#output-file-test_summarylog)
  - [Customization](#customization)
- [Frame Classification](#frame-classification)
  - [Features](#classification-features)
  - [Categories](#categories)
  - [Usage](#classification-usage)
  - [Classification Workflow](#classification-workflow)
  - [Output](#classification-output)
- [License](#license)

## Overview
This project provides tools for building computer vision datasets from RTSP camera streams. It includes:

1. **Frame Collector**: A script that connects to an RTSP camera stream, captures frames at specified intervals, and saves them as JPEG images.
2. **Frame Classifier**: A tool for manually organizing captured frames into predefined categories, essential for preparing training data for AI models.

Both tools work together to streamline the creation of labeled datasets for computer vision tasks.

## Features
- **Adjustable Capture Intervals:** Modify the time between frame captures.
- **Adjustable JPEG Quality:** Configure the quality of saved JPEG images.
- **Configurable Connection:** Easily adjust the RTSP connection parameters (username, password, IP, port, and stream path) via an environment file.
- **Round-Based Data Management:** Automatically manages rounds of data capture with unique frame naming.
- **Metadata Logging:** Detailed session logs are appended to `test_summary.log`.
- **Manual Classification:** Intuitive interface for categorizing frames into predefined classes.
- **Classification Tracking:** Saves classification data in JSON format and organizes images into category folders.

## Requirements
- Python 3.x
- [OpenCV](https://opencv.org/) (`cv2`)
- [python-dotenv](https://pypi.org/project/python-dotenv/)
- [NumPy](https://numpy.org/)
- [PIL/Pillow](https://pillow.readthedocs.io/en/stable/)
- Standard Python libraries: `os`, `re`, `time`, `shutil`, `datetime`, `json`, `sys`

## Configuration
1. **Install Dependencies:**
   ```bash
   pip install opencv-python python-dotenv pillow numpy
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

## Frame Capture

### Execution
Run the capture script using:
```bash
python frame_collector.py
```

The script will:
- Connect to the RTSP stream.
- Capture frames at the configured interval (default is one frame every 2 seconds).
- Save the frames in the `rtsp_test_frames` directory.
- Log session metadata to `test_summary.log`.

### Code Explanation

#### Environment and RTSP Connection
- **Environment Variables:**
  The script uses dotenv to load camera credentials and stream parameters from the `.env` file.
- **RTSP URL Construction:**
  It constructs the RTSP URL and masks sensitive information (e.g., the password) in console outputs.

#### Round Management
- **Round ID Determination:**
  The function `get_next_round_id()` determines the next round ID by:
  - Reading the current round from `test_round_state.txt`.
  - Scanning the image directory for existing rounds if the state file is missing or contains invalid data.
- **State Update:**
  After the capture session, the current round ID is saved back to `test_round_state.txt` for future runs.

#### Frame Capture and Saving
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

#### Metadata Logging
- **Statistics Calculation:**
  After capturing, the script calculates the total number of frames saved, total storage size, and average size per frame.
- **Log File:**
  Metadata including start and end times, configured duration versus actual duration, capture interval, JPEG quality, and storage statistics is appended to `test_summary.log`.

### Output File: `test_summary.log`
The `test_summary.log` file consolidates detailed session metadata, including:
- **Session Timings:** Start and end times.
- **Duration:** Configured test duration versus the actual runtime.
- **Capture Parameters:** Capture interval and JPEG quality.
- **Statistics:** Number of frames saved, total data size, and average size per frame.

This log is critical for analyzing the performance of each capture session and making adjustments for future runs.

### Customization
The capture script allows you to easily modify key parameters:
- **Capture Interval:** Change the time between frame captures.
- **JPEG Quality:** Adjust the quality setting for JPEG image saving.
- **RTSP Connection Parameters:** Update the `.env` file to modify connection details.
- **Test Duration:** Set the overall runtime of the capture session.

## Frame Classification

### Classification Features
- **Intuitive UI:** Visual interface for efficient frame classification
- **Keyboard Navigation:** Arrow keys for frame browsing and numeric keys for classification
- **Batch Navigation:** Quickly jump ahead 10, 100, or 1000 frames
- **Classification Persistence:** Progress is automatically saved to a JSON file
- **Organized Output:** Classified frames are copied to category-specific directories
- **Visual Feedback:** Status display shows classification progress and statistics
- **Robust Image Loading:** Uses PIL for better handling of file paths and image formats

### Categories
The classifier supports the following predefined categories:
1. **forno_enchendo**: Furnace filling phase
2. **sinterizacao_acontecendo**: Sintering process underway
3. **despejo_acontecendo**: Dumping/discharge in progress
4. **panela_voltando_posicao_normal**: Pan returning to normal position
5. **forno_vazio**: Empty furnace

### Usage
Run the classification tool using:
```bash
python frame_classifier.py
```

Before running, update the `frames_directory` variable in the script to point to the directory containing your captured frames (default is the `rtsp_test_frames` directory).

### Classification Workflow
1. **Navigation:** Use arrow keys to browse through frames
   - Left/Right arrows: Navigate one frame at a time
   - Key 7: Jump ahead 10 frames
   - Key 8: Jump ahead 100 frames
   - Key 9: Jump ahead 1000 frames
2. **Classification:** Press keys 1-5 to classify frames into their respective categories
3. **Quitting:** Press 'Q' to save and exit

The interface shows:
- Current frame number and navigation status
- Classification status of the current frame
- Available categories with their current counts
- Navigation controls

### Classification Output
The classifier produces two main outputs:
1. **`classifications.json`**: A JSON file containing metadata for all classified frames
2. **Categorized directories**: Inside the `amostras-classes` directory, frames are organized into subdirectories by category

The JSON file includes detailed information for each classified frame:
- Category ID and name
- Original and classified file paths
- Frame metadata (round ID, frame number, timestamp)
- Classification timestamp

## License
MIT License
