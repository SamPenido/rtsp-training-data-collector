import cv2
import numpy as np
from config import COLORS, CATEGORIES, SUBCATEGORIES # Import constants

def draw_semi_transparent_rect(img, start_point, end_point, color, alpha=0.7):
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
    if img is None: return None # Handle case where image might be None
    overlay = img.copy()
    cv2.rectangle(overlay, start_point, end_point, color, -1)
    cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0, img)
    return img

def draw_text_with_shadow(img, text, position, font_scale=1.0, color=None,
                           thickness=1, shadow_color=(0, 0, 0), shadow_offset=2,
                           font=cv2.FONT_HERSHEY_SIMPLEX):
    """
    Draw text with a shadow for better visibility against any background.

    Args:
        img: Image to draw on
        text: Text to draw
        position: (x, y) position
        font_scale: Font scale
        color: Text color (defaults to COLORS['text'])
        thickness: Text thickness
        shadow_color: Color of the shadow
        shadow_offset: Shadow offset in pixels
        font: Font type

    Returns:
        Modified image
    """
    if img is None: return None # Handle case where image might be None
    if color is None:
        color = COLORS['text']

    # Draw the shadow
    shadow_position = (position[0] + shadow_offset, position[1] + shadow_offset)
    cv2.putText(img, text, shadow_position, font, font_scale, shadow_color, thickness + 1, cv2.LINE_AA)

    # Draw the text
    cv2.putText(img, text, position, font, font_scale, color, thickness, cv2.LINE_AA)

    return img

def draw_overlay_ui(img, current_frame_filename, current_index, total_frames,
                    classifications, stats, current_subcategory, show_help, show_stats):
    """
    Draw minimalistic overlay UI on the image.

    Args:
        img: Image to display (can be None)
        current_frame_filename (str): Filename of the current frame
        current_index (int): Current frame index (0-based)
        total_frames (int): Total number of frames
        classifications (dict): Dictionary of classified frames
        stats (dict): Dictionary of classification statistics
        current_subcategory (str or None): Currently selected subcategory ('i', 'm', 'f')
        show_help (bool): Whether to display the help overlay
        show_stats (bool): Whether to display the stats overlay

    Returns:
        Image with overlay UI (or a placeholder if img was None)
    """
    if img is None:
        # Create a black placeholder image if the original image failed to load
        img = np.zeros((720, 1280, 3), dtype=np.uint8) # Use default dimensions or pass them in?
        draw_text_with_shadow(img, "Error loading image", (50, 360), font_scale=1.5, color=COLORS['warning'])

    # Get image dimensions
    h, w = img.shape[:2]

    # Create a copy of the image for overlay
    display_img = img.copy()

    # --- MINIMAL UI ELEMENTS (Always visible) ---

    # Draw frame counter in top-left corner
    frame_info = f"Frame: {current_index + 1}/{total_frames}"
    text_size = cv2.getTextSize(frame_info, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
    draw_semi_transparent_rect(
        display_img, (10, 10), (text_size[0] + 30, 35), (0, 0, 0), 0.6
    )
    draw_text_with_shadow(
        display_img, frame_info, (15, 30), font_scale=0.7, color=COLORS['header']
    )

    # --- Category List (Top-Left below Frame Counter) ---
    category_start_y = 45
    category_width = 250
    category_height = 25 + (len(CATEGORIES) * 20)
    category_start_x = 10

    draw_semi_transparent_rect(
        display_img, (category_start_x, category_start_y),
        (category_start_x + category_width, category_start_y + category_height),
        (0, 0, 0), 0.6
    )
    draw_text_with_shadow(
        display_img, "CATEGORIES:", (category_start_x + 5, category_start_y + 20),
        font_scale=0.7, color=COLORS['highlight']
    )

    y_pos = category_start_y + 40
    for key, category in CATEGORIES.items():
        cat_text = f"{key}: {category}"
        is_highlighted = False
        if current_frame_filename in classifications:
            if classifications[current_frame_filename]["category_name"] == category:
                is_highlighted = True
        draw_text_with_shadow(
            display_img, cat_text, (category_start_x + 5, y_pos),
            font_scale=0.6, color=COLORS['success'] if is_highlighted else COLORS['text']
        )
        y_pos += 20

    # Draw controls hint in bottom-right
    hint_text = "H: Help | S: Stats | Q: Quit"
    text_size = cv2.getTextSize(hint_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)[0]
    draw_semi_transparent_rect(
        display_img, (w - text_size[0] - 20, h - 35), (w - 10, h - 10), (0, 0, 0), 0.6
    )
    draw_text_with_shadow(
        display_img, hint_text, (w - text_size[0] - 15, h - 15),
        font_scale=0.6, color=COLORS['info']
    )

    # Show current subcategory if one is selected
    if current_subcategory:
        subcat_text = f"Subcategory: {SUBCATEGORIES[current_subcategory]}"
        text_size = cv2.getTextSize(subcat_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 1)[0]
        draw_semi_transparent_rect(
            display_img, (10, h - 40), (text_size[0] + 30, h - 15), (0, 0, 0), 0.6
        )
        draw_text_with_shadow(
            display_img, subcat_text, (15, h - 20), font_scale=0.7, color=COLORS['subcategory']
        )

    # --- MODAL UI ELEMENTS (Only visible when requested) ---

    # Draw help overlay if requested
    if show_help:
        draw_semi_transparent_rect(
            display_img, (int(w*0.1), int(h*0.1)), (int(w*0.9), int(h*0.9)), (0, 0, 0), 0.85
        )
        help_title = "KEYBOARD CONTROLS"
        draw_text_with_shadow(
            display_img, help_title, (int(w*0.5 - len(help_title)*7), int(h*0.15)),
            font_scale=1.0, color=COLORS['highlight']
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
            draw_text_with_shadow(display_img, cmd, (int(w*0.2), y_pos), font_scale=0.7)
            y_pos += 35

        y_pos = int(h * 0.25) # Reset y_pos for category list on the right
        for key, category in CATEGORIES.items():
            cat_text = f"{key}: {category}"
            draw_text_with_shadow(display_img, cat_text, (int(w*0.55), y_pos), font_scale=0.7)
            y_pos += 35

        close_text = "Press H again to close this help screen"
        draw_text_with_shadow(
            display_img, close_text, (int(w*0.5 - len(close_text)*4), int(h*0.85)),
            font_scale=0.6, color=COLORS['info']
        )

    # Draw stats overlay if requested
    elif show_stats:
        draw_semi_transparent_rect(
            display_img, (int(w*0.1), int(h*0.1)), (int(w*0.9), int(h*0.9)), (0, 0, 0), 0.85
        )
        stats_title = "CLASSIFICATION STATISTICS"
        draw_text_with_shadow(
            display_img, stats_title, (int(w*0.5 - len(stats_title)*7), int(h*0.15)),
            font_scale=1.0, color=COLORS['highlight']
        )

        y_pos = int(h * 0.25)
        null_count = stats.get("null", 0)
        null_text = f"NULL: {null_count} frames"
        draw_text_with_shadow(display_img, null_text, (int(w*0.3), y_pos), font_scale=0.8)
        y_pos += 50

        for cat_id in ['1', '2', '3', '4', '5']:
            cat_name = CATEGORIES[cat_id]
            cat_total = 0
            for subcat in SUBCATEGORIES.values():
                cat_total += stats.get(f"{cat_name}_{subcat}", 0)

            draw_text_with_shadow(
                display_img, f"{cat_id}: {cat_name} (Total: {cat_total})",
                (int(w*0.3), y_pos), font_scale=0.8
            )
            y_pos += 30

            for subcat_id, subcat_name in SUBCATEGORIES.items():
                count = stats.get(f"{cat_name}_{subcat_name}", 0)
                draw_text_with_shadow(
                    display_img, f"  {subcat_name}: {count} frames",
                    (int(w*0.35), y_pos), font_scale=0.7
                )
                y_pos += 25
            y_pos += 15

        total_classified = len(classifications)
        percent = (total_classified / total_frames * 100) if total_frames > 0 else 0
        total_text = f"Total: {total_classified}/{total_frames} frames classified ({percent:.1f}%)"
        draw_text_with_shadow(
            display_img, total_text, (int(w*0.3), int(h*0.8)),
            font_scale=0.8, color=COLORS['header']
        )

        close_text = "Press S again to close this statistics view"
        draw_text_with_shadow(
            display_img, close_text, (int(w*0.5 - len(close_text)*4), int(h*0.85)),
            font_scale=0.6, color=COLORS['info']
        )

    # If this frame is classified, show a small indicator
    if current_frame_filename in classifications:
        indicator_color = COLORS['success']
        cv2.circle(display_img, (w//2, 15), 8, indicator_color, -1) # Small green dot top-center

    return display_img
