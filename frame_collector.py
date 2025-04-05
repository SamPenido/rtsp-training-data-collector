import cv2
import cv2
import os
import re # Import regex module
import time
import shutil
from datetime import datetime
from dotenv import load_dotenv

def calculate_directory_size(directory_path):
    """Calculates the total size of all files in a directory."""
    total_size = 0
    try:
        for item in os.listdir(directory_path):
            item_path = os.path.join(directory_path, item)
            if os.path.isfile(item_path):
                total_size += os.path.getsize(item_path)
    except FileNotFoundError:
        print(f"Error: Directory not found at {directory_path}")
        return 0
    except Exception as e:
        print(f"An error occurred while calculating directory size: {e}")
        return 0
    return total_size

# --- Round State Management ---
STATE_FILENAME = "test_round_state.txt"
SUMMARY_FILENAME = "test_summary.log"

def get_next_round_id(state_file=STATE_FILENAME, image_dir="rtsp_test_frames"):
    """Determines the next round ID robustly.
    1. Tries reading from the state file.
    2. If state file fails, scans image directory for highest round ID in filenames.
    3. Returns max(state_round, file_round) + 1.
    """
    last_round_from_state = 0
    try:
        with open(state_file, 'r') as f:
            last_round_from_state = int(f.read().strip())
        print(f"Read last round {last_round_from_state} from state file.")
    except FileNotFoundError:
        print("State file not found. Checking image filenames for round ID.")
        last_round_from_state = 0
    except ValueError:
        print("Invalid content in state file. Checking image filenames.")
        last_round_from_state = 0
    except Exception as e:
        print(f"Error reading state file '{state_file}': {e}. Checking image filenames.")
        last_round_from_state = 0

    max_round_from_files = 0
    try:
        if os.path.isdir(image_dir):
            # Regex to find 'round_<number>_' at the start of the filename
            pattern = re.compile(r"^round_(\d+)_.*\.jpg$")
            max_round_found = 0
            for fname in os.listdir(image_dir):
                match = pattern.match(fname)
                if match:
                    round_num = int(match.group(1))
                    if round_num > max_round_found:
                        max_round_found = round_num
            max_round_from_files = max_round_found
            if max_round_from_files > 0:
                print(f"Found max round {max_round_from_files} from image filenames.")
            else:
                 print(f"No valid round filenames found in '{image_dir}'.")
        else:
            print(f"Image directory '{image_dir}' not found for round check.")

    except Exception as e:
        print(f"Error scanning image directory '{image_dir}': {e}")
        max_round_from_files = 0 # Default to 0 if scan fails

    # Determine the definitive last round
    last_round = max(last_round_from_state, max_round_from_files)
    next_round = last_round + 1
    print(f"Determined next round ID: {next_round} (based on last round {last_round})")
    return next_round


def save_round_id(round_id, state_file=STATE_FILENAME):
    """Saves the current round ID to the state file."""
    try:
        with open(state_file, 'w') as f:
            f.write(str(round_id))
    except Exception as e:
        print(f"Error writing state file '{state_file}': {e}")

# --- Metadata Logging ---
def write_metadata(filename, round_id, rtsp_url_masked, start_time_dt, end_time_dt, duration_minutes, interval, quality, frames_saved, total_kb, avg_kb):
    """Appends the test metadata for the current round to the summary file."""
    start_str = start_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    end_str = end_time_dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    actual_duration_seconds = (end_time_dt - start_time_dt).total_seconds()

    metadata_content = f"""
--- Round {round_id} Start: {start_str} ---
Camera URL: {rtsp_url_masked}
Configured Duration: {duration_minutes} minutes
Actual Duration: {actual_duration_seconds:.2f} seconds
Capture Interval: {interval} seconds
JPEG Quality: {quality}
Frames Saved in Round: {frames_saved}
Total Size (Round): {total_kb:.2f} KB
Average Size per Frame (Round): {avg_kb:.2f} KB
--- Round {round_id} End: {end_str} ---
"""
    try:
        # Append to the summary file
        with open(filename, 'a') as f:
            f.write(metadata_content)
        print(f"Metadata for Round {round_id} appended to: {filename}")
    except Exception as e:
        print(f"Error appending metadata to file '{filename}': {e}")


def main():
    start_time_dt = datetime.now() # Record exact start time
    # Load environment variables from .env file
    load_dotenv()

    # Get camera credentials and stream path
    username = os.getenv("CAMERA_USERNAME")
    password = os.getenv("CAMERA_PASSWORD")
    ip = os.getenv("CAMERA_IP")
    port = os.getenv("CAMERA_PORT")
    stream_path = os.getenv("RTSP_STREAM_PATH")

    if not all([username, password, ip, port, stream_path]):
        print("Error: Camera credentials or stream path not found in .env file.")
        print("Please ensure CAMERA_USERNAME, CAMERA_PASSWORD, CAMERA_IP, CAMERA_PORT, and RTSP_STREAM_PATH are set.")
        return

    # Construct the RTSP URL
    rtsp_url = f"rtsp://{username}:{password}@{ip}:{port}{stream_path}"
    print(f"Connecting to RTSP stream: rtsp://{username}:******@{ip}:{port}{stream_path}") # Hide password in output

    # --- Test Parameters ---
    # Duration for this specific test run (24 hours)
    # Note: This is a long duration for testing purposes. Adjust as needed.
    test_duration_minutes = 1440 # Duration for this specific test run (24 hours)
    test_duration_seconds = test_duration_minutes * 60
    interval_seconds = 2
    jpeg_quality = 75
    output_dir = "rtsp_test_frames"
    print(f"Configured to run for {test_duration_minutes} minutes ({test_duration_seconds} seconds).")
    print(f"Capturing 1 frame every {interval_seconds} seconds.")
    print(f"Saving JPEGs with quality {jpeg_quality}.")

    # --- Determine Round ID ---
    current_round_id = get_next_round_id()
    print(f"Starting Test Round: {current_round_id}")

    # --- Ensure output directory exists (don't clear) ---
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"Ensured output directory exists: '{output_dir}'")
    except Exception as e:
        print(f"Error creating directory '{output_dir}': {e}")
        return

    # Connect to the RTSP stream
    cap = cv2.VideoCapture(rtsp_url)

    if not cap.isOpened():
        print(f"Error: Could not open RTSP stream at {rtsp_url}")
        return

    print(f"Successfully connected to stream. Starting capture for {test_duration_minutes} minutes...")

    frames_saved_count = 0
    round_filenames = [] # List to store filenames saved in this round
    last_save_time = 0 # Initialize to ensure the first frame is saved immediately
    start_run_time = time.time()
    end_run_time = start_run_time + test_duration_seconds

    while time.time() < end_run_time:
        ret, frame = cap.read()

        if not ret:
            print(f"Warning: Could not read frame. Stream might have ended or encountered an issue. Stopping capture.")
            break # Stop if we can't read frames

        current_time = time.time()

        # Check if the interval has passed since the last save
        if current_time - last_save_time >= interval_seconds:
            # Save the original frame as JPEG without any processing
            # Use Round ID, Frame ID (per round), and Unix timestamp in milliseconds for the filename
            frame_id_in_round = frames_saved_count + 1
            timestamp_ms = int(current_time * 1000)
            # Format: round_<round_id>_<frame_id_in_round>_<timestamp_ms>.jpg
            frame_filename = os.path.join(output_dir, f"round_{current_round_id}_{frame_id_in_round}_{timestamp_ms}.jpg")
            try:
                # Ensure frame is not empty before saving
                if frame is not None and frame.size > 0:
                    # Save with specified JPEG quality
                    cv2.imwrite(frame_filename, frame, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
                    frames_saved_count += 1 # Increment only after successful save attempt logic
                    round_filenames.append(frame_filename) # Add saved filename to list
                    last_save_time = current_time # Update the last save time
                    print(f"Saved frame {frame_id_in_round} (Round {current_round_id}): {frame_filename} (Quality {jpeg_quality}) at {time.strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"Warning: Read an empty frame, skipping save for Round {current_round_id}, Frame {frame_id_in_round}.")

            except Exception as e:
                print(f"Error saving frame {frame_id_in_round} (Round {current_round_id}): {e}")

        # Small sleep to prevent high CPU usage from constant reading
        # Adjust if needed, but keep it small relative to the interval
        time.sleep(0.05) # 50ms sleep

    # Release the video capture object
    cap.release()
    end_time_dt = datetime.now() # Record exact end time
    run_duration = (end_time_dt - start_time_dt).total_seconds()
    print(f"Finished capturing frames. Capture ran for {run_duration:.2f} seconds.")
    print("Finished capturing frames. Released video stream.")

    # Calculate size based *only* on files saved in this round
    total_bytes_this_round = 0
    if round_filenames: # Check if any files were saved in this round
        for fname in round_filenames:
            try:
                total_bytes_this_round += os.path.getsize(fname)
            except FileNotFoundError:
                print(f"Warning: File {fname} not found during size calculation.")
            except Exception as e:
                print(f"Warning: Error getting size for file {fname}: {e}")

    total_kb = 0
    average_kb_per_frame = 0
    if frames_saved_count > 0 and total_bytes_this_round > 0:
        total_kb = total_bytes_this_round / 1024
        average_kb_per_frame = total_kb / frames_saved_count # Use frames_saved_count for average

        print("\n--- Storage Test Results (Round) ---")
        print(f"Total frames saved: {frames_saved_count}")
        print(f"Total size of frames: {total_kb:.2f} KB")
        print(f"Average size per frame: {average_kb_per_frame:.2f} KB")
    else:
        print("\nNo frames were saved. Cannot calculate storage size.")

    # Construct masked URL for logging
    rtsp_url_masked = f"rtsp://{username}:******@{ip}:{port}{stream_path}"

    # Write metadata file (append to summary)
    write_metadata(
        filename=SUMMARY_FILENAME, # Use the constant summary filename
        round_id=current_round_id,
        rtsp_url_masked=rtsp_url_masked, # Pass the masked URL
        start_time_dt=start_time_dt,
        end_time_dt=end_time_dt,
        duration_minutes=test_duration_minutes,
        interval=interval_seconds,
        quality=jpeg_quality,
        frames_saved=frames_saved_count,
        total_kb=total_kb,
        avg_kb=average_kb_per_frame
    )

    # Save the current round ID for the next run
    save_round_id(current_round_id)

if __name__ == "__main__":
    main()
