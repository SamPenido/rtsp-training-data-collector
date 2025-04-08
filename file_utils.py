import os
import json
import sys
import re
import numpy as np
from PIL import Image
from config import DEFAULT_CLASSIFICATION_FILE

def load_classifications(json_file_path=DEFAULT_CLASSIFICATION_FILE):
    """Load existing classifications from JSON file if it exists."""
    classifications = {}
    stats = {} # Initialize stats here as well, maybe return it? Or let the main class handle stats. Let's return it for now.

    if os.path.exists(json_file_path):
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                classifications = json.load(f)
            print(f"Loaded {len(classifications)} existing classifications from {json_file_path}")

            # Calculate stats based on loaded classifications (needs CATEGORIES and SUBCATEGORIES, maybe pass them in?)
            # For simplicity, let's skip calculating stats here and let the main class do it after loading.

        except Exception as e:
            print(f"Error loading classifications from {json_file_path}: {e}")
            classifications = {} # Reset on error
    return classifications

def save_classifications(classifications, json_file_path=DEFAULT_CLASSIFICATION_FILE):
    """Save current classifications to JSON file."""
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(classifications, f, indent=4, ensure_ascii=False)
        # Keep print statement in the main class for better context? Or here? Let's keep it here for now.
        # print(f"Saved {len(classifications)} classifications to {json_file_path}")
        return True
    except Exception as e:
        print(f"Error saving classifications to {json_file_path}: {e}")
        return False

def load_frame_files(frames_dir):
    """Load all frame filenames from the input directory, sorted by round and frame number."""
    if not os.path.exists(frames_dir):
        print(f"Error: Directory {frames_dir} does not exist.")
        return [] # Return empty list instead of exiting

    frame_files = []
    try:
        # Get all jpg files in the directory
        all_files = []
        for file in os.listdir(frames_dir):
            if file.lower().endswith('.jpg') and file.startswith('round_'):
                all_files.append(file)

        # Extract round and frame numbers for sorting
        processed_files = []
        for filename in all_files:
            match = re.match(r'round_(\d+)_(\d+)_\d+\.jpg', filename)
            if match:
                round_id = int(match.group(1))
                frame_num = int(match.group(2))
                processed_files.append((filename, round_id, frame_num))

        # Sort by round_id and then by frame_num
        processed_files.sort(key=lambda x: (x[1], x[2]))

        # Extract just the filenames in sorted order
        frame_files = [item[0] for item in processed_files]

        print(f"Found {len(frame_files)} frames in {frames_dir} matching the pattern.")
        if frame_files:
            first_frame = frame_files[0]
            last_frame = frame_files[-1]
            print(f"First frame: {first_frame}")
            print(f"Last frame: {last_frame}")

    except Exception as e:
        print(f"Error loading frame files from {frames_dir}: {e}")
        frame_files = [] # Reset on error

    return frame_files

def load_image_with_pil(image_path, suppress_warnings=True):
    """
    Load an image using PIL and convert to OpenCV format (BGR numpy array).
    Handles non-ASCII characters in paths better than cv2.imread.

    Args:
        image_path (str): Path to the image file
        suppress_warnings (bool): If True, suppresses PIL loading errors.

    Returns:
        numpy.ndarray or None: The loaded image in OpenCV BGR format or None if failed.
    """
    try:
        # Use PIL to open the image
        pil_image = Image.open(image_path)
        # Convert PIL image to OpenCV format (numpy array)
        opencv_image = np.array(pil_image)
        # Convert RGB (PIL default) to BGR (OpenCV default)
        if len(opencv_image.shape) == 3 and opencv_image.shape[2] == 3:
            # Check if it's RGB before converting
            if pil_image.mode == 'RGB':
                 opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGB2BGR)
            # If it's already BGR (less common for PIL), do nothing
            # elif pil_image.mode == 'BGR':
            #    pass
        elif len(opencv_image.shape) == 3 and opencv_image.shape[2] == 4:
             # Handle RGBA images (convert to BGR, discarding alpha)
             opencv_image = cv2.cvtColor(opencv_image, cv2.COLOR_RGBA2BGR)
        # Grayscale images remain grayscale

        return opencv_image
    except FileNotFoundError:
         if not suppress_warnings:
            print(f"Error: Image file not found at {image_path}")
         return None
    except Exception as e:
        if not suppress_warnings:
            print(f"Error loading image {os.path.basename(image_path)} with PIL: {e}")
        return None

# Need to import cv2 for the color conversions in load_image_with_pil
import cv2
