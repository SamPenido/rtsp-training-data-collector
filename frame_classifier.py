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
    Supports reclassification of previously classified frames.
    Includes NULL category and event phase subcategories (inicio, meio, fim).
    Features an overlay-style UI for better image visibility.
    """
    
    # Main categories with simplified naming
    CATEGORIES = {
        '0': 'null',
        '1': 'forno_enchendo',
        '2': 'sinterizacao_acontecendo',
        '3': 'despejo_acontecendo',
        '4': 'panela_voltando_posicao_normal',
        '5': 'forno_vazio'
    }
    
    # Subcategories for event phases
    SUBCATEGORIES = {
        'i': 'inicio',
        'm': 'meio',
        'f': 'fim'
    }
    
    # Define colors for better visibility
    COLORS = {
        'bg': (20, 20, 20),           # Dark background
        'header': (50, 200, 255),     # Blue headers
        'text': (255, 255, 255),      # White text
        'highlight': (0, 255, 255),   # Yellow for highlights
        'success': (50, 255, 50),     # Green for success
        'warning': (255, 50, 50),     # Red for warnings
        'info': (180, 180, 180),      # Light gray for info
        'subcategory': (255, 127, 0)  # Orange for subcategories
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
        
        # Initialize stats - now with subcategories
        self.stats = {}
        for cat in self.CATEGORIES.values():
            if cat == 'null':
                # NULL category doesn't have subcategories
                self.stats[cat] = 0
            else:
                # Other categories have subcategories
                for subcat in self.SUBCATEGORIES.values():
                    self.stats[f"{cat}_{subcat}"] = 0
        
        self.suppress_warnings = True
        self.window_name = "Frame Classifier"
        self.window_width = 1280
        self.window_height = 720
        
        # Current subcategory selection (None until a subcategory is selected)
        self.current_subcategory = None
        
        # UI control variables
        self.show_help = False
        self.show_stats = False
        
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
                    subcategory = info.get("subcategory_name", None)
                    
                    if category == "null":
                        self.stats[category] += 1
                    elif subcategory and f"{category}_{subcategory}" in self.stats:
                        self.stats[f"{category}_{subcategory}"] += 1
                        
                print("Current classification stats:")
                for cat, count in self.stats.items():
                    if count > 0:
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
    
    def _classify_frame(self, frame_filename, category, subcategory=None):
        """
        Classify a frame without copying it.
        Only stores metadata in the classifications dictionary.
        If the frame was already classified, it's reclassified with the new category.
        
        Args:
            frame_filename (str): Filename of the frame
            category (str): Category ID ('0' to '5')
            subcategory (str, optional): Subcategory ID ('i', 'm', 'f')
        """
        if category not in self.CATEGORIES:
            print(f"Invalid category: {category}")
            return False
        
        # For categories other than NULL (0), a subcategory is required
        if category != '0' and subcategory not in self.SUBCATEGORIES:
            print(f"Invalid subcategory: {subcategory}. For non-NULL categories, please select a subcategory (i, m, f).")
            return False
            
        category_name = self.CATEGORIES[category]
        subcategory_name = self.SUBCATEGORIES.get(subcategory) if subcategory else None
        source_path = os.path.join(self.frames_dir, frame_filename)
        
        # Check if this is a reclassification
        is_reclassification = frame_filename in self.classifications
        old_category_name = None
        old_subcategory_name = None
        
        if is_reclassification:
            # Get the previous category to update stats
            old_category_name = self.classifications[frame_filename].get("category_name")
            old_subcategory_name = self.classifications[frame_filename].get("subcategory_name")
            
            # Only update if the classification actually changed
            if old_category_name == category_name and old_subcategory_name == subcategory_name:
                print(f"Frame already classified as '{category_name}'{f' ({subcategory_name})' if subcategory_name else ''}. No changes made.")
                return False
                
            # Decrement the count for the old category
            if old_category_name == "null":
                self.stats[old_category_name] -= 1
            elif old_subcategory_name and f"{old_category_name}_{old_subcategory_name}" in self.stats:
                self.stats[f"{old_category_name}_{old_subcategory_name}"] -= 1
        
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
        
        # Create classification data with or without subcategory
        classification_data = {
            "category_id": category,
            "category_name": category_name,
            "original_path": source_path,
            "metadata": metadata,
            "classified_at": datetime.now().isoformat()
        }
        
        # Add subcategory information if provided
        if subcategory and subcategory_name:
            classification_data["subcategory_id"] = subcategory
            classification_data["subcategory_name"] = subcategory_name
        
        # Save the classification
        self.classifications[frame_filename] = classification_data
        
        # Update stats for the new category
        if category_name == "null":
            self.stats[category_name] += 1
            stat_key = category_name
        else:
            stat_key = f"{category_name}_{subcategory_name}"
            self.stats[stat_key] += 1
        
        # Output classification information
        if is_reclassification:
            old_display = old_category_name
            if old_subcategory_name and old_category_name != "null":
                old_display = f"{old_category_name} ({old_subcategory_name})"
                
            new_display = category_name
            if subcategory_name and category_name != "null":
                new_display = f"{category_name} ({subcategory_name})"
                
            print(f"Reclassified from '{old_display}' to '{new_display}' (Total: {self.stats[stat_key]})")
        else:
            if category_name == "null":
                print(f"Classified as: '{category_name}' (Total: {self.stats[stat_key]})")
            else:
                print(f"Classified as: '{category_name} ({subcategory_name})' (Total: {self.stats[stat_key]})")
        
        # Save classifications after each update
        self._save_classifications()
        return True
    
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
            
    def _draw_semi_transparent_rect(self, img, start_point, end_point, color, alpha=0.7):
        """
        Draw a semi-transparent rectangle on the image.
        
        Args:
            img: Image to draw on
            start_point: Top-left corner (x, y)
            end_point: Bottom-right corner (x, y)
            color: Rectangle color (B, G, R)
            alpha: Transparency level (0.0 to 1.0)
            
        Returns:
            Modified image
        """
        # Create a separate image for the overlay
        overlay = img.copy()
        
        # Draw the filled rectangle on the overlay
        cv2.rectangle(overlay, start_point, end_point, color, -1)
        
        # Blend the overlay with the original image
        cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
        
        return img
    
    def _draw_text_with_shadow(self, img, text, position, font_scale=1.0, color=None, 
                               thickness=1, shadow_color=(0, 0, 0), shadow_offset=2, 
                               font=cv2.FONT_HERSHEY_SIMPLEX):
        """
        Draw text with a shadow for better visibility against any background.
        
        Args:
            img: Image to draw on
            text: Text to draw
            position: (x, y) position
            font_scale: Font scale
            color: Text color
            thickness: Text thickness
            shadow_color: Color of the shadow
            shadow_offset: Shadow offset in pixels
            font: Font type
            
        Returns:
            Modified image
        """
        if color is None:
            color = self.COLORS['text']
            
        # Draw the shadow
        shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)
        cv2.putText(img, text, shadow_position, font, font_scale, shadow_color, thickness+1)
        
        # Draw the text
        cv2.putText(img, text, position, font, font_scale, color, thickness)
        
        return img
            
    def _draw_overlay_ui(self, img, current_frame):
        """
        Draw minimalistic overlay UI on the image - simplified version.
        Shows only essential information by default with access to more details via menus.
        
        Args:
            img: Image to display
            current_frame: The filename of the current frame
            
        Returns:
            Image with overlay UI
        """
        if img is None:
            # Create a black placeholder image
            img = np.zeros((720, 1280, 3), dtype=np.uint8)
            
        # Get image dimensions
        h, w = img.shape[:2]
        
        # Create a copy of the image for overlay
        display_img = img.copy()
        
        # --- MINIMAL UI ELEMENTS (Always visible) ---
        
        # Draw frame counter in top-left corner with semi-transparent background
        frame_info = f"Frame: {self.current_index + 1}/{len(self.frame_files)}"
        text_size = cv2.getTextSize(frame_info, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
        
        self._draw_semi_transparent_rect(
            display_img, 
            (10, 10), 
            (text_size[0] + 30, 35), 
            (0, 0, 0), 
            0.6
        )
        
        self._draw_text_with_shadow(
            display_img, 
            frame_info, 
            (15, 30), 
            font_scale=0.7, 
            color=self.COLORS['header']
        )

        # --- Category List (Moved to Top-Left below Frame Counter) ---
        category_start_y = 45  # Start below the frame counter (which ends at y=35)
        category_width = 250   # Adjust width as needed
        category_height = 25 + (len(self.CATEGORIES) * 20) # Header + categories
        category_start_x = 10

        # Draw background for categories
        self._draw_semi_transparent_rect(
            display_img,
            (category_start_x, category_start_y),
            (category_start_x + category_width, category_start_y + category_height),
            (0, 0, 0),
            0.6
        )

        # Draw category header
        self._draw_text_with_shadow(
            display_img,
            "CATEGORIES:",
            (category_start_x + 5, category_start_y + 20), # Position header inside the box
            font_scale=0.7,
            color=self.COLORS['highlight']
        )

        # Draw each category (including NULL)
        y_pos = category_start_y + 40 # Start drawing categories below the header
        for key, category in self.CATEGORIES.items():
            cat_text = f"{key}: {category}"

            # Check if this frame is classified with this category
            is_highlighted = False
            if current_frame in self.classifications:
                if self.classifications[current_frame]["category_name"] == category:
                    is_highlighted = True
            self._draw_text_with_shadow(
                display_img,
                cat_text,
                (category_start_x + 5, y_pos), # Position categories inside the box
                font_scale=0.6,
                color=self.COLORS['success'] if is_highlighted else self.COLORS['text']
            )
            y_pos += 20

        # Draw controls hint in bottom-right
        hint_text = "H: Help | S: Stats"
        text_size = cv2.getTextSize(hint_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
        
        self._draw_semi_transparent_rect(
            display_img, 
            (w - text_size[0] - 20, h - 35), 
            (w - 10, h - 10), 
            (0, 0, 0), 
            0.6
        )
        
        self._draw_text_with_shadow(
            display_img, 
            hint_text, 
            (w - text_size[0] - 15, h - 15), 
            font_scale=0.6, 
            color=self.COLORS['info']
        )
        
        # Show current subcategory if one is selected
        if self.current_subcategory:
            subcat_text = f"Subcategory: {self.SUBCATEGORIES[self.current_subcategory]}"
            text_size = cv2.getTextSize(subcat_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
            
            self._draw_semi_transparent_rect(
                display_img, 
                (10, h - 40), 
                (text_size[0] + 30, h - 15), 
                (0, 0, 0), 
                0.6
            )
            
            self._draw_text_with_shadow(
                display_img, 
                subcat_text, 
                (15, h - 20), 
                font_scale=0.7, 
                color=self.COLORS['subcategory']
            )
        
        # --- MODAL UI ELEMENTS (Only visible when requested) ---
        
        # Draw help overlay if requested
        if self.show_help:
            # Semi-transparent dark background
            self._draw_semi_transparent_rect(
                display_img, 
                (int(w*0.1), int(h*0.1)), 
                (int(w*0.9), int(h*0.9)), 
                (0, 0, 0), 
                0.85
            )
            
            # Help content
            help_title = "KEYBOARD CONTROLS"
            self._draw_text_with_shadow(
                display_img, 
                help_title, 
                (int(w*0.5 - len(help_title)*7), int(h*0.15)), 
                font_scale=1.0, 
                color=self.COLORS['highlight']
            )
            
            commands = [
                "◄ ► : Navigate frames",
                "0: Classify as NULL (no event)",
                "1-5: Classify into categories (requires subcategory)",
                "I/M/F: Select subcategory (inicio/meio/fim)",
                "H: Toggle this help screen",
                "S: Toggle statistics view",
                "7: Jump forward 10 frames",
                "8: Jump forward 100 frames", 
                "9: Jump forward 1000 frames",
                "Q: Quit and save"
            ]
            
            y_pos = int(h * 0.25)
            for cmd in commands:
                self._draw_text_with_shadow(
                    display_img, 
                    cmd, 
                    (int(w*0.2), y_pos), 
                    font_scale=0.7
                )
                y_pos += 35
                
            # Category reference
            y_pos = int(h * 0.25)
            for key, category in self.CATEGORIES.items():
                cat_text = f"{key}: {category}"
                self._draw_text_with_shadow(
                    display_img, 
                    cat_text, 
                    (int(w*0.55), y_pos), 
                    font_scale=0.7
                )
                y_pos += 35
                
            # Close instruction
            close_text = "Press H again to close this help screen"
            self._draw_text_with_shadow(
                display_img, 
                close_text, 
                (int(w*0.5 - len(close_text)*4), int(h*0.85)), 
                font_scale=0.6, 
                color=self.COLORS['info']
            )
        
        # Draw stats overlay if requested
        elif self.show_stats:
            # Semi-transparent dark background
            self._draw_semi_transparent_rect(
                display_img, 
                (int(w*0.1), int(h*0.1)), 
                (int(w*0.9), int(h*0.9)), 
                (0, 0, 0), 
                0.85
            )
            
            # Stats content
            stats_title = "CLASSIFICATION STATISTICS"
            self._draw_text_with_shadow(
                display_img, 
                stats_title, 
                (int(w*0.5 - len(stats_title)*7), int(h*0.15)), 
                font_scale=1.0, 
                color=self.COLORS['highlight']
            )
            
            # Draw statistics for each category
            y_pos = int(h * 0.25)
            
            # First NULL category
            null_count = self.stats.get("null", 0)
            null_text = f"NULL: {null_count} frames"
            self._draw_text_with_shadow(
                display_img, 
                null_text, 
                (int(w*0.3), y_pos), 
                font_scale=0.8
            )
            y_pos += 50
            
            # Other categories with subcategories
            for cat_id in ['1', '2', '3', '4', '5']:
                cat_name = self.CATEGORIES[cat_id]
                
                # Calculate total for this category
                cat_total = 0
                for subcat in self.SUBCATEGORIES.values():
                    cat_total += self.stats.get(f"{cat_name}_{subcat}", 0)
                
                # Category header with total count
                self._draw_text_with_shadow(
                    display_img, 
                    f"{cat_id}: {cat_name} (Total: {cat_total})", 
                    (int(w*0.3), y_pos), 
                    font_scale=0.8
                )
                y_pos += 30
                
                # Subcategory breakdown
                for subcat_id, subcat_name in self.SUBCATEGORIES.items():
                    count = self.stats.get(f"{cat_name}_{subcat_name}", 0)
                    self._draw_text_with_shadow(
                        display_img, 
                        f"  {subcat_name}: {count} frames", 
                        (int(w*0.35), y_pos), 
                        font_scale=0.7
                    )
                    y_pos += 25
                
                y_pos += 15
                
            # Total classified frames
            total_classified = len(self.classifications)
            total_frames = len(self.frame_files)
            percent = (total_classified / total_frames * 100) if total_frames > 0 else 0
            
            total_text = f"Total: {total_classified}/{total_frames} frames classified ({percent:.1f}%)"
            
            self._draw_text_with_shadow(
                display_img, 
                total_text, 
                (int(w*0.3), int(h*0.8)), 
                font_scale=0.8, 
                color=self.COLORS['header']
            )
            
            # Close instruction
            close_text = "Press S again to close this statistics view"
            self._draw_text_with_shadow(
                display_img, 
                close_text, 
                (int(w*0.5 - len(close_text)*4), int(h*0.85)), 
                font_scale=0.6, 
                color=self.COLORS['info']
            )
        
        # If this frame is classified, show a small indicator
        if current_frame in self.classifications:
            cat_name = self.classifications[current_frame]["category_name"]
            subcat_name = self.classifications[current_frame].get("subcategory_name", "")
            
            # Just a small dot indicator in top-center of screen
            indicator_color = self.COLORS['success']
            cv2.circle(display_img, (w//2, 15), 8, indicator_color, -1)
        
        return display_img
    
    def run(self):
        """
        Run the classification interface with arrow key navigation.
        """
        print("\n=== Frame Classification Tool ===")
        print("Keyboard Controls:")
        print("  ← → Arrow Keys: Navigate between frames")
        print("  0-5: Classify frames into categories")
        print("    0 - null (no event)")
        for key in ['1', '2', '3', '4', '5']:
            print(f"    {key} - {self.CATEGORIES[key]}")
        print("  I/M/F: Select subcategory (inicio/meio/fim) - required for categories 1-5")
        print("  H: Toggle help screen")
        print("  S: Toggle statistics view")
        print("  7: Advance 10 frames")
        print("  8: Advance 100 frames")
        print("  9: Advance 1000 frames")
        print("  Q: Quit")
        print("==================================\n")
        print("Note: You can reclassify frames by pressing a different category key (0-5)\n")
        print("Workflow: First select a subcategory (I/M/F), then press a category key (1-5).\n")
        print("For NULL category (0), no subcategory selection is needed.\n")
        
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
                subcat_name = self.classifications[current_frame].get("subcategory_name", "")
                
                if cat_name == "null":
                    classification_info = f" (Classified as: {cat_name})"
                else:
                    classification_info = f" (Classified as: {cat_name} - {subcat_name})"
            
            # Display minimal frame info in console
            print(f"Frame {self.current_index + 1}/{len(self.frame_files)}: {current_frame}{classification_info}")
            
            # Read and display the image using PIL
            img = self._load_image_with_pil(frame_path)
            
            # Create overlay UI
            display_img = self._draw_overlay_ui(img, current_frame)
            
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
                
            # Toggle help screen
            elif key_lower in [ord('h'), ord('H')]:
                self.show_help = not self.show_help
                if self.show_help:
                    self.show_stats = False  # Close stats if open
                
            # Toggle statistics screen
            elif key_lower in [ord('s'), ord('S')]:
                self.show_stats = not self.show_stats
                if self.show_stats:
                    self.show_help = False  # Close help if open
                
            # Subcategory selection (I, M, F keys)
            elif key_lower in [ord('i'), ord('I')]:
                self.current_subcategory = 'i'
                print(f"Selected subcategory: {self.SUBCATEGORIES['i']} (inicio)")
                
            elif key_lower in [ord('m'), ord('M')]:
                self.current_subcategory = 'm'
                print(f"Selected subcategory: {self.SUBCATEGORIES['m']} (meio)")
                
            elif key_lower in [ord('f'), ord('F')]:
                self.current_subcategory = 'f'
                print(f"Selected subcategory: {self.SUBCATEGORIES['f']} (fim)")
                
            # Category selection (0-5 keys)
            elif chr(key_lower) in self.CATEGORIES:
# Only process if help/stats screens are not showing
                if not self.show_help and not self.show_stats:
                    category = chr(key_lower)
                    was_classified = current_frame in self.classifications
                    
                    # For NULL (0) category, no subcategory needed
                    if category == '0':
                        if self._classify_frame(current_frame, category):
                            if not was_classified:
                                self.current_index += 1
                    
                    # For other categories (1-5), subcategory is required
                    else:
                        if self.current_subcategory:
                            if self._classify_frame(current_frame, category, self.current_subcategory):
                                if not was_classified:
                                    self.current_index += 1
                        else:
                            print("Please select a subcategory first (I/M/F) for non-NULL categories.")
                
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
            
            # Ensure we don't go past the end of the list
            if self.current_index >= len(self.frame_files):
                self.current_index = len(self.frame_files) - 1
        
        cv2.destroyAllWindows()
        print("Classification complete.")
        self._save_classifications()


if __name__ == "__main__":
    frames_directory = r"C:\Users\Usuário\Documents\GitHub\renavam-crawler-mg-test\yolov8-object-logger\rtsp_test_frames"
    
    # Create and run the classifier
    classifier = FrameClassifier(frames_directory)
    classifier.run()
