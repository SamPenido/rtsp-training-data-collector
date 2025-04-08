import os
import cv2
import sys
import re
from datetime import datetime
import numpy as np

# Import configurations and utilities from modules
from config import (
    CATEGORIES, SUBCATEGORIES, DEFAULT_CLASSIFICATION_FILE,
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT
)
from file_utils import (
    load_classifications, save_classifications,
    load_frame_files, load_image_with_pil
)
from ui_utils import draw_overlay_ui

class FrameClassifier:
    """
    A tool for manually classifying frames saved from an RTSP stream.
    Uses modularized components for configuration, file operations, and UI.
    """

    def __init__(self, frames_dir, classification_file=DEFAULT_CLASSIFICATION_FILE):
        """
        Initialize the FrameClassifier.

        Args:
            frames_dir (str): Directory containing the frames to classify.
            classification_file (str): Path to the JSON file for classifications.
        """
        self.frames_dir = frames_dir
        self.json_file = classification_file
        self.current_index = 0
        self.frame_files = []
        self.classifications = {}
        self.stats = {} # Statistics will be calculated after loading

        self.suppress_warnings = True # Suppress PIL/OpenCV loading warnings
        self.window_name = "Frame Classifier"
        self.window_width = DEFAULT_WINDOW_WIDTH
        self.window_height = DEFAULT_WINDOW_HEIGHT

        # Current subcategory selection (None until selected)
        self.current_subcategory = None

        # UI control variables
        self.show_help = False
        self.show_stats = False

        # Load existing data
        self._load_initial_data()

        if not self.frame_files:
            print(f"No suitable image files found in {frames_dir}. Exiting.")
            sys.exit(1)

        print(f"Initialization complete. Ready to classify {len(self.frame_files)} frames.")

    def _initialize_stats(self):
        """Initialize the statistics dictionary based on categories and subcategories."""
        self.stats = {}
        for cat_id, cat_name in CATEGORIES.items():
            if cat_name == 'null':
                self.stats[cat_name] = 0
            else:
                for subcat_id, subcat_name in SUBCATEGORIES.items():
                    self.stats[f"{cat_name}_{subcat_name}"] = 0
        print("Statistics initialized.")

    def _update_stats_from_classifications(self):
        """Recalculate statistics based on the current classifications."""
        self._initialize_stats() # Reset stats first
        if not self.classifications:
            print("No classifications loaded to update stats.")
            return

        for frame_filename, info in self.classifications.items():
            category_name = info.get("category_name")
            subcategory_name = info.get("subcategory_name", None)

            if not category_name: continue # Skip if category name is missing

            if category_name == "null":
                if category_name in self.stats:
                    self.stats[category_name] += 1
                else:
                    print(f"Warning: Category '{category_name}' not found in initial stats.")
            elif subcategory_name:
                stat_key = f"{category_name}_{subcategory_name}"
                if stat_key in self.stats:
                    self.stats[stat_key] += 1
                else:
                     print(f"Warning: Stat key '{stat_key}' not found in initial stats.")
            # else: # Handle cases where non-null might be missing subcategory if needed
            #    print(f"Warning: Frame {frame_filename} classified as non-null ('{category_name}') but missing subcategory.")

        print("Statistics updated from loaded classifications.")
        # Optionally print current stats summary
        # for cat, count in self.stats.items():
        #     if count > 0:
        #         print(f"  {cat}: {count} frames")


    def _load_initial_data(self):
        """Load frame files and existing classifications."""
        print(f"Loading frames from: {self.frames_dir}")
        self.frame_files = load_frame_files(self.frames_dir)

        if not self.frame_files:
            return # Exit if no frames found

        print(f"\nLoading classifications from: {self.json_file}")
        self.classifications = load_classifications(self.json_file)

        # Calculate stats based on loaded classifications
        self._update_stats_from_classifications()


    def _classify_frame(self, frame_filename, category_id, subcategory_id=None):
        """
        Classify a frame and update statistics.

        Args:
            frame_filename (str): Filename of the frame.
            category_id (str): Category ID ('0' to '5').
            subcategory_id (str, optional): Subcategory ID ('i', 'm', 'f').

        Returns:
            bool: True if classification was successful (new or reclassification), False otherwise.
        """
        if category_id not in CATEGORIES:
            print(f"Invalid category ID: {category_id}")
            return False

        category_name = CATEGORIES[category_id]
        subcategory_name = None

        # For categories other than NULL (0), a subcategory is required
        if category_name != 'null':
            if subcategory_id not in SUBCATEGORIES:
                print(f"Invalid or missing subcategory ID: {subcategory_id}. Required for non-NULL categories.")
                return False
            subcategory_name = SUBCATEGORIES[subcategory_id]

        source_path = os.path.join(self.frames_dir, frame_filename)

        # Check for reclassification
        is_reclassification = frame_filename in self.classifications
        old_category_name = None
        old_subcategory_name = None

        if is_reclassification:
            old_info = self.classifications[frame_filename]
            old_category_name = old_info.get("category_name")
            old_subcategory_name = old_info.get("subcategory_name")

            # Check if classification actually changed
            if old_category_name == category_name and old_subcategory_name == subcategory_name:
                print(f"Frame already classified as '{category_name}'{f' ({subcategory_name})' if subcategory_name else ''}. No change.")
                return False # Indicate no change was made

            # Decrement count for the old classification in stats
            if old_category_name == "null":
                if old_category_name in self.stats: self.stats[old_category_name] -= 1
            elif old_subcategory_name:
                old_stat_key = f"{old_category_name}_{old_subcategory_name}"
                if old_stat_key in self.stats: self.stats[old_stat_key] -= 1

        # Extract metadata from filename (assuming format: round_X_Y_timestamp.jpg)
        match = re.match(r"round_(\d+)_(\d+)_(\d+)\.jpg", frame_filename)
        metadata = {
            "round_id": match.group(1) if match else "unknown",
            "frame_number": match.group(2) if match else "unknown",
            "timestamp": match.group(3) if match else "unknown"
        }

        # Create new classification data
        classification_data = {
            "category_id": category_id,
            "category_name": category_name,
            "original_path": source_path, # Store original path for reference
            "metadata": metadata,
            "classified_at": datetime.now().isoformat()
        }
        if subcategory_id and subcategory_name:
            classification_data["subcategory_id"] = subcategory_id
            classification_data["subcategory_name"] = subcategory_name

        # Update classifications dictionary
        self.classifications[frame_filename] = classification_data

        # Increment count for the new classification in stats
        new_stat_key = category_name if category_name == "null" else f"{category_name}_{subcategory_name}"
        if new_stat_key in self.stats:
            self.stats[new_stat_key] += 1
        else:
             print(f"Warning: Stat key '{new_stat_key}' not found during increment.")


        # Print confirmation message
        new_display = f"'{category_name}'" + (f" ({subcategory_name})" if subcategory_name else "")
        if is_reclassification:
            old_display = f"'{old_category_name}'" + (f" ({old_subcategory_name})" if old_subcategory_name else "")
            print(f"Reclassified from {old_display} to {new_display} (Total {new_stat_key}: {self.stats.get(new_stat_key, 0)})")
        else:
            print(f"Classified as: {new_display} (Total {new_stat_key}: {self.stats.get(new_stat_key, 0)})")

        # Attempt to save classifications immediately
        if not save_classifications(self.classifications, self.json_file):
            print("Warning: Failed to save classifications after update.")
        # else:
            # print(f"Saved {len(self.classifications)} classifications.") # Optional: confirmation

        return True # Indicate successful classification/reclassification


    def _print_help(self):
        """Prints the initial help message to the console."""
        print("\n=== Frame Classification Tool ===")
        print("Keyboard Controls (in OpenCV window):")
        print("  ← → Arrow Keys: Navigate between frames")
        print("  0-5: Classify frames into categories")
        print("    0 - null (no event)")
        for key in ['1', '2', '3', '4', '5']:
            print(f"    {key} - {CATEGORIES[key]}")
        print("  I/M/F: Select subcategory (inicio/meio/fim) - required for categories 1-5")
        print("  H: Toggle help overlay")
        print("  S: Toggle statistics overlay")
        print("  7: Jump forward 10 frames")
        print("  8: Jump forward 100 frames")
        print("  9: Jump forward 1000 frames")
        print("  Q: Quit and save")
        print("==================================\n")
        print("Note: You can reclassify frames by pressing a different category key.")
        print("Workflow: Select subcategory (I/M/F) THEN press category key (1-5).")
        print("For NULL (0), no subcategory is needed.\n")

    def run(self):
        """Run the main classification loop."""
        self._print_help()

        # Create and configure OpenCV window
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)

        # Suppress OpenCV errors if needed (handled by PIL loading now)
        if self.suppress_warnings:
            # os.environ["OPENCV_LOG_LEVEL"] = "ERROR" # May not be needed now
            print("Image loading warnings suppressed.")

        while 0 <= self.current_index < len(self.frame_files):
            current_frame_filename = self.frame_files[self.current_index]
            frame_path = os.path.join(self.frames_dir, current_frame_filename)

            # Display minimal info in console
            classification_info = ""
            if current_frame_filename in self.classifications:
                info = self.classifications[current_frame_filename]
                cat_name = info.get("category_name", "N/A")
                subcat_name = info.get("subcategory_name")
                classification_info = f" (Classified: {cat_name}{f' - {subcat_name}' if subcat_name else ''})"
            # print(f"\rFrame {self.current_index + 1}/{len(self.frame_files)}: {current_frame_filename}{classification_info}", end="")


            # Load image using utility function
            img = load_image_with_pil(frame_path, self.suppress_warnings)

            # Draw UI using utility function
            display_img = draw_overlay_ui(
                img, current_frame_filename, self.current_index, len(self.frame_files),
                self.classifications, self.stats, self.current_subcategory,
                self.show_help, self.show_stats
            )

            # Show the image
            cv2.imshow(self.window_name, display_img)

            # Wait for key input
            key = cv2.waitKeyEx(0) # Use waitKeyEx for arrow keys
            key_lower = key & 0xFF # Get ASCII value for regular keys

            # --- Process Key Input ---
            if key_lower == ord('q'):
                print("\nExiting...")
                break

            # Toggle Help/Stats overlays
            elif key_lower == ord('h'):
                self.show_help = not self.show_help
                if self.show_help: self.show_stats = False # Mutually exclusive
            elif key_lower == ord('s'):
                self.show_stats = not self.show_stats
                if self.show_stats: self.show_help = False # Mutually exclusive

            # Subcategory Selection
            elif key_lower == ord('i'):
                self.current_subcategory = 'i'
                print(f"\nSelected subcategory: {SUBCATEGORIES['i']}")
            elif key_lower == ord('m'):
                self.current_subcategory = 'm'
                print(f"\nSelected subcategory: {SUBCATEGORIES['m']}")
            elif key_lower == ord('f'):
                self.current_subcategory = 'f'
                print(f"\nSelected subcategory: {SUBCATEGORIES['f']}")

            # Category Classification (only if help/stats not shown)
            elif not self.show_help and not self.show_stats and chr(key_lower) in CATEGORIES:
                category_id = chr(key_lower)
                was_classified = current_frame_filename in self.classifications

                if category_id == '0': # NULL category
                    if self._classify_frame(current_frame_filename, category_id):
                         # Advance only if it was newly classified (not reclassified)
                         # Let's always advance after classification for simplicity now
                         self.current_index += 1
                else: # Non-NULL categories require subcategory
                    if self.current_subcategory:
                        if self._classify_frame(current_frame_filename, category_id, self.current_subcategory):
                            # Advance only if it was newly classified
                            # Let's always advance after classification for simplicity now
                            self.current_index += 1
                    else:
                        print("\nPlease select a subcategory (I/M/F) before classifying with 1-5.")

            # Navigation Keys
            elif key in [2555904, 65363, 83]:  # Right arrow
                self.current_index += 1
                # print("\nNext frame")
            elif key in [2424832, 65361, 81]:  # Left arrow
                self.current_index -= 1
                # print("\nPrevious frame")
            elif key_lower == ord('7'): # Jump +10
                self.current_index = min(self.current_index + 10, len(self.frame_files) - 1)
                print(f"\nJumped to frame {self.current_index + 1}")
            elif key_lower == ord('8'): # Jump +100
                self.current_index = min(self.current_index + 100, len(self.frame_files) - 1)
                print(f"\nJumped to frame {self.current_index + 1}")
            elif key_lower == ord('9'): # Jump +1000
                self.current_index = min(self.current_index + 1000, len(self.frame_files) - 1)
                print(f"\nJumped to frame {self.current_index + 1}")

            # else: # Debug unknown keys
            #     if key != -1: print(f"\nUnknown key pressed: {key} (ASCII: {key_lower})")


            # Boundary checks for index
            if self.current_index < 0:
                self.current_index = 0
            if self.current_index >= len(self.frame_files):
                # Option 1: Stop at the last frame
                self.current_index = len(self.frame_files) - 1
                print("\nReached the last frame.")
                # Option 2: Loop back or exit? Let's stop.

        # Cleanup
        cv2.destroyAllWindows()
        # Final save attempt (might be redundant if saving after each classification)
        if save_classifications(self.classifications, self.json_file):
             print(f"\nFinal classifications saved to {self.json_file}.")
        else:
             print(f"\nWarning: Failed to save final classifications to {self.json_file}.")

        print("Classification process finished.")


if __name__ == "__main__":
    # --- Configuration ---
    # It's better to get this from command line arguments or a config file,
    # but hardcoding for now as in the original script.
    # IMPORTANT: Ensure this path is correct for your system.
    frames_directory = r"C:\Users\Usuário\Documents\GitHub\renavam-crawler-mg-test\yolov8-object-logger\rtsp_test_frames"
    classification_output_file = "classifications.json" # Use the default or specify another

    # --- Check if frames directory exists ---
    if not os.path.isdir(frames_directory):
        print(f"Error: Frames directory not found at '{frames_directory}'")
        print("Please ensure the path is correct and the directory exists.")
        sys.exit(1)

    # --- Run the classifier ---
    print("Starting Frame Classifier...")
    classifier = FrameClassifier(frames_directory, classification_output_file)
    classifier.run()
