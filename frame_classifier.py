import os
import cv2
import json
import sys
import re
from datetime import datetime
import numpy as np
from PIL import Image

class FrameClassifier:
    """
    A tool for manually classifying frames saved from an RTSP stream into predefined categories.
    Uses PIL for robust image loading and supports arrow key navigation.
    Only stores classification metadata in JSON without copying the actual image files.
    """
    
    # Class categories with simplified naming (no accents, underscores)
    CATEGORIES = {
        '1': 'forno_enchendo',
        '2': 'sinterizacao_acontecendo',
        '3': 'despejo_acontecendo',
        '4': 'panela_voltando_posicao_normal',
        '5': 'forno_vazio'
    }
    
    # Define colors for better visibility
    COLORS = {
        'bg': (30, 30, 30),         # Dark gray background
        'header': (50, 200, 255),   # Blue headers
        'text': (255, 255, 255),    # White text
        'highlight': (0, 255, 255), # Yellow for highlights
        'success': (50, 255, 50),   # Green for success
        'warning': (50, 50, 255),   # Red for warnings
        'info': (180, 180, 180)     # Light gray for info
    }
    
    def __init__(self, frames_dir):
        """
        Initialize the FrameClassifier.
        
        Args:
            frames_dir (str): Directory containing the frames to classify
        """
        self.frames_dir = frames_dir
        self.current_index = 0
        self.frame_files = []
        self.classifications = {}
        self.json_file = "classifications.json"
        self.stats = {cat: 0 for cat in self.CATEGORIES.values()}
        self.suppress_warnings = True
        self.window_name = "Frame Classifier"
        self.window_width = 1280
        self.window_height = 800
        
        # Load existing classifications if available
        self._load_classifications()
        
        # Load all frame filenames
        self._load_frame_files()
        
        if not self.frame_files:
            print(f"No image files found in {frames_dir}")
            sys.exit(1)
            
        print(f"Loaded {len(self.frame_files)} frames from {frames_dir}")
        
    def _load_classifications(self):
        """Load existing classifications from JSON file if it exists."""
        if os.path.exists(self.json_file):
            try:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    self.classifications = json.load(f)
                print(f"Loaded {len(self.classifications)} existing classifications")
                
                # Update stats
                for info in self.classifications.values():
                    category = info.get("category_name")
                    if category in self.stats:
                        self.stats[category] += 1
                        
                print("Current classification stats:")
                for cat, count in self.stats.items():
                    print(f"  {cat}: {count} frames")
                    
            except Exception as e:
                print(f"Error loading classifications: {e}")
                self.classifications = {}
        
    def _save_classifications(self):
        """Save current classifications to JSON file."""
        try:
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump(self.classifications, f, indent=4, ensure_ascii=False)
            print(f"Saved {len(self.classifications)} classifications to {self.json_file}")
        except Exception as e:
            print(f"Error saving classifications: {e}")
    
    def _load_frame_files(self):
        """Load all frame filenames from the input directory, sorted by round and frame number."""
        if not os.path.exists(self.frames_dir):
            print(f"Error: Directory {self.frames_dir} does not exist.")
            sys.exit(1)
            
        try:
            # Get all jpg files in the directory
            all_files = []
            for file in os.listdir(self.frames_dir):
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
            self.frame_files = [item[0] for item in processed_files]
            
            print(f"Found {len(self.frame_files)} frames matching the pattern round_<round_id>_<frame_number>_<timestamp>.jpg")
            if self.frame_files:
                first_frame = self.frame_files[0]
                last_frame = self.frame_files[-1]
                print(f"First frame: {first_frame}")
                print(f"Last frame: {last_frame}")
                
        except Exception as e:
            print(f"Error loading frame files: {e}")
            sys.exit(1)
    
    def _classify_frame(self, frame_filename, category):
        """
        Classify a frame without copying it.
        Only stores metadata in the classifications dictionary.
        
        Args:
            frame_filename (str): Filename of the frame
            category (str): Category ID ('1' to '5')
        """
        if category not in self.CATEGORIES:
            print(f"Invalid category: {category}")
            return
            
        category_name = self.CATEGORIES[category]
        source_path = os.path.join(self.frames_dir, frame_filename)
        
        # Extract frame metadata from filename
        match = re.match(r"round_(\d+)_(\d+)_(\d+)\.jpg", frame_filename)
        if match:
            round_id = match.group(1)
            frame_number = match.group(2)
            timestamp = match.group(3)
        else:
            round_id = "unknown"
            frame_number = "unknown"
            timestamp = "unknown"
            
        metadata = {
            "round_id": round_id,
            "frame_number": frame_number,
            "timestamp": timestamp
        }
        
        # Save the classification with metadata
        self.classifications[frame_filename] = {
            "category_id": category,
            "category_name": category_name,
            "original_path": source_path,
            "metadata": metadata,
            "classified_at": datetime.now().isoformat()
        }
        
        # Update stats
        self.stats[category_name] += 1
        
        print(f"Classified as: {category_name} (Total: {self.stats[category_name]})")
        
        # Save classifications after each update
        self._save_classifications()
    
    def _load_image_with_pil(self, image_path):
        """
        Load an image using PIL and convert to OpenCV format.
        This provides better support for non-ASCII characters in paths.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            numpy.ndarray or None: The loaded image in OpenCV format or None if failed
        """
        try:
            # Use PIL to open the image which handles Unicode paths better
            pil_image = Image.open(image_path)
            # Convert PIL image to OpenCV format (numpy array with BGR)
            opencv_image = np.array(pil_image)
            # Convert RGB to BGR (OpenCV uses BGR)
            if len(opencv_image.shape) == 3 and opencv_image.shape[2] == 3:
                opencv_image = opencv_image[:, :, ::-1].copy()
            return opencv_image
        except Exception as e:
            if not self.suppress_warnings:
                print(f"PIL cannot load image: {e}")
            return None
            
    def _draw_text_with_outline(self, img, text, position, font_scale=1.0, color=None, 
                              thickness=2, outline_color=(0, 0, 0), 
                              outline_thickness=4, font=cv2.FONT_HERSHEY_DUPLEX):
        """
        Draw text with a thick outline for better visibility on any background.
        
        Args:
            img: Image to draw on
            text: Text to draw
            position: (x, y) position
            font_scale: Font scale
            color: Text color
            thickness: Text thickness
            outline_color: Color of the outline
            outline_thickness: Thickness of the outline
            font: Font type
            
        Returns:
            Modified image
        """
        if color is None:
            color = self.COLORS['text']
            
        # Draw the outline
        cv2.putText(img, text, position, font, font_scale, outline_color, outline_thickness)
        
        # Draw the text on top of the outline
        cv2.putText(img, text, position, font, font_scale, color, thickness)
        
        return img
            
    def _create_status_panel(self, img, current_frame):
        """
        Create a status panel with large, bold text for better visibility.
        
        Args:
            img (numpy.ndarray): The image to display
            current_frame (str): The filename of the current frame
            
        Returns:
            numpy.ndarray: The image with status panel
        """
        if img is None:
            # Create a black placeholder image
            img = np.zeros((480, 640, 3), dtype=np.uint8)
            
        # Get image dimensions
        img_height, img_width = img.shape[:2]
        
        # Calculate panel dimensions
        panel_height = 200  # Height of status panel
        total_height = img_height + panel_height
        
        # Create a new image with space for the panel
        display_img = np.zeros((total_height, img_width, 3), dtype=np.uint8)
        
        # Set a dark gray background for the panel
        display_img[0:panel_height, :] = self.COLORS['bg']
        
        # Copy the original image below the panel
        display_img[panel_height:total_height, :] = img
        
        # Add a divider line
        cv2.line(display_img, (0, panel_height), (img_width, panel_height), self.COLORS['highlight'], 2)
        
        # Frame information - large and prominent with outline
        frame_info = f"Frame: {self.current_index + 1} / {len(self.frame_files)}"
        self._draw_text_with_outline(
            display_img, frame_info, (20, 40), 
            font_scale=1.0, color=self.COLORS['header'], 
            thickness=2, outline_thickness=4
        )
        
        # Add file info 
        file_info = f"File: {current_frame}"
        self._draw_text_with_outline(
            display_img, file_info, (20, 80), 
            font_scale=0.7, color=self.COLORS['info'], 
            thickness=2, outline_thickness=3
        )
        
        # Display classification status with bold text
        if current_frame in self.classifications:
            cat_name = self.classifications[current_frame]["category_name"]
            status_text = f"Status: Classified as '{cat_name}'"
            status_color = self.COLORS['success']
        else:
            status_text = "Status: NOT CLASSIFIED"
            status_color = self.COLORS['warning']
            
        self._draw_text_with_outline(
            display_img, status_text, (20, 120), 
            font_scale=0.9, color=status_color, 
            thickness=2, outline_thickness=4
        )
        
        # Draw a background rectangle for controls to improve visibility
        controls_bg_start = (10, 145)
        controls_bg_end = (img_width // 2 - 50, 195)
        cv2.rectangle(display_img, controls_bg_start, controls_bg_end, (0, 0, 0), -1)
        cv2.rectangle(display_img, controls_bg_start, controls_bg_end, self.COLORS['highlight'], 1)
        
        # Display keyboard instructions
        instructions_text = "CONTROLS:"
        self._draw_text_with_outline(
            display_img, instructions_text, (20, 165), 
            font_scale=0.8, color=self.COLORS['highlight'], 
            thickness=2, outline_thickness=3
        )
        
        # Display navigation controls with bold outlined text
        nav_text = "◄ ► : Navigate | 7:+10 | 8:+100 | 9:+1000 | Q:Quit"
        self._draw_text_with_outline(
            display_img, nav_text, (20, 190), 
            font_scale=0.7, color=self.COLORS['text'], 
            thickness=2, outline_thickness=3
        )
        
        # Category information - right side with background
        cat_bg_start = (img_width // 2, 10)
        cat_bg_end = (img_width - 10, panel_height - 10)
        cv2.rectangle(display_img, cat_bg_start, cat_bg_end, (0, 0, 0), -1)
        cv2.rectangle(display_img, cat_bg_start, cat_bg_end, self.COLORS['highlight'], 1)
        
        # Categories header
        cat_header_text = "CATEGORIES:"
        self._draw_text_with_outline(
            display_img, cat_header_text, (img_width // 2 + 15, 35), 
            font_scale=0.8, color=self.COLORS['highlight'], 
            thickness=2, outline_thickness=3
        )
        
        # List all categories with bold outlined text
        y_pos = 65
        for key, category in self.CATEGORIES.items():
            count = self.stats[category]
            cat_text = f"{key}: {category} ({count})"
            self._draw_text_with_outline(
                display_img, cat_text, (img_width // 2 + 20, y_pos), 
                font_scale=0.7, color=self.COLORS['text'], 
                thickness=2, outline_thickness=3
            )
            y_pos += 25
        
        return display_img
    
    def run(self):
        """
        Run the classification interface with arrow key navigation.
        """
        print("\n=== Frame Classification Tool ===")
        print("Keyboard Controls:")
        print("  ← → Arrow Keys: Navigate between frames")
        print("  1-5: Classify frames into categories")
        for key, category in self.CATEGORIES.items():
            print(f"    {key} - {category}")
        print("  7: Advance 10 frames")
        print("  8: Advance 100 frames")
        print("  9: Advance 1000 frames")
        print("  Q: Quit")
        print("==================================\n")
        
        # Create window with specific size
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)
        
        # Disable OpenCV error output
        if self.suppress_warnings:
            print("Suppressing OpenCV warnings about image loading...")
            os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
        
        while 0 <= self.current_index < len(self.frame_files):
            current_frame = self.frame_files[self.current_index]
            frame_path = os.path.join(self.frames_dir, current_frame)
            
            # Check if this frame has already been classified
            classification_info = ""
            if current_frame in self.classifications:
                cat_name = self.classifications[current_frame]["category_name"]
                classification_info = f" (Classified as: {cat_name})"
            
            # Display minimal frame info in console
            print(f"Frame {self.current_index + 1}/{len(self.frame_files)}: {current_frame}{classification_info}")
            
            # Read and display the image using PIL
            img = self._load_image_with_pil(frame_path)
            
            # Create status panel
            display_img = self._create_status_panel(img, current_frame)
            
            # Show the image
            cv2.imshow(self.window_name, display_img)
            
            # Handle empty image case
            if img is None:
                print(f"Could not read image: {frame_path}")
                
            # Wait for key input
            key = cv2.waitKeyEx(0)
            key_lower = key & 0xFF  # Get the ASCII value
            
            # Process key input
            if key_lower == ord('q') or key_lower == ord('Q'):
                print("Exiting...")
                break
            elif chr(key_lower) in self.CATEGORIES:
                category = chr(key_lower)
                self._classify_frame(current_frame, category)
                self.current_index += 1  # Move to next frame after classification
            # Arrow keys - check for various codes they might generate
            elif key in [2555904, 65363, 83]:  # Right arrow key (Windows/Linux/Mac)
                self.current_index += 1
                print("Next frame")
            elif key in [2424832, 65361, 81]:  # Left arrow key (Windows/Linux/Mac)
                self.current_index -= 1
                print("Previous frame")
                if self.current_index < 0:
                    self.current_index = 0
            elif key_lower == ord('7'):
                # Advance 10 frames
                self.current_index = min(self.current_index + 10, len(self.frame_files) - 1)
                print(f"Advanced to frame {self.current_index + 1}")
            elif key_lower == ord('8'):
                # Advance 100 frames
                self.current_index = min(self.current_index + 100, len(self.frame_files) - 1)
                print(f"Advanced to frame {self.current_index + 1}")
            elif key_lower == ord('9'):
                # Advance 1000 frames
                self.current_index = min(self.current_index + 1000, len(self.frame_files) - 1)
                print(f"Advanced to frame {self.current_index + 1}")
            else:
                # For debugging unknown keys
                print(f"Key pressed: {key}")
        
        cv2.destroyAllWindows()
        print("Classification complete.")
        self._save_classifications()


if __name__ == "__main__":
    frames_directory = r"C:\Users\Usuário\Documents\GitHub\renavam-crawler-mg-test\yolov8-object-logger\rtsp_test_frames"
    
    # Create and run the classifier
    classifier = FrameClassifier(frames_directory)
    classifier.run()
