import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
from PIL import ImageGrab
import time

GAME_WINDOW_TITLE = "Core Keeper"               # Game window title
TARGET_IMAGE_PATH = "icon.png"                  # Path to fish icon image
SEARCH_REGION_OFFSET = (1200, 450, 300, 300)    # Relative region (x, y, width, height)
LOOP_DELAY = 1.0                                # Delay between each loop
THRESHOLD = 0.8                                 # Confidence threshold for image matching
DEBUG_MODE = False

def find_game_window(title):
    """Find the game window by its title."""
    windows = gw.getWindowsWithTitle(title)
    return windows[0] if windows else None

def get_window_region(window):
    """Get the absolute screen region of the game window."""
    return (window.left, window.top, window.right, window.bottom)

def calculate_search_region(window_region, relative_offset):
    """Calculate the search region dynamically based on the window size."""
    x, y, right, bottom = window_region
    width = right - x
    height = bottom - y

    # Scale the relative offset based on the window size
    offset_x = int(relative_offset[0] * width)
    offset_y = int(relative_offset[1] * height)
    offset_width = int(relative_offset[2] * width)
    offset_height = int(relative_offset[3] * height)

    return (x + offset_x, y + offset_y, x + offset_x + offset_width, y + offset_y + offset_height)

def search_image_in_region(target_img, region, threshold):
    """Search for target image inside a screen region. Return image frame and match info."""
    screenshot = ImageGrab.grab(bbox=region)
    screenshot_rgb = np.array(screenshot)
    screenshot_gray = cv2.cvtColor(screenshot_rgb, cv2.COLOR_BGR2GRAY)

    result = cv2.matchTemplate(screenshot_gray, target_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    fish_found = False
    fish_screen_pos = None

    if max_val >= threshold:
        top_left = max_loc
        h, w = target_img.shape
        bottom_right = (top_left[0] + w, top_left[1] + h)

        # Convert to absolute screen coordinates
        screen_x = region[0] + top_left[0] + w // 2
        screen_y = region[1] + top_left[1] + h // 2
        fish_screen_pos = (screen_x, screen_y)

        # Draw red rectangle for debug
        cv2.rectangle(screenshot_rgb, top_left, bottom_right, (0, 0, 255), 2)
        fish_found = True
        print(f"Fish icon found at {top_left} (confidence: {max_val:.2f})")
    else:
        print("Fish icon not found.")

    screenshot_bgr = cv2.cvtColor(screenshot_rgb, cv2.COLOR_RGB2BGR)
    return screenshot_bgr, fish_found, fish_screen_pos

def cast_fishing_line():
    """Simulate holding the right mouse button to cast the fishing line."""
    print("Casting fishing line...")
    pyautogui.mouseDown(button='right')
    time.sleep(1.3)
    pyautogui.mouseUp(button='right')

def resize_target_image(target_img, window_region, reference_resolution):
    """
    Resize the target image based on the current window size and a reference resolution.
    :param target_img: The original target image (icon2.png).
    :param window_region: The current game window region (x1, y1, x2, y2).
    :param reference_resolution: The resolution the target image was designed for (width, height).
    :return: Resized target image.
    """
    window_width = window_region[2] - window_region[0]
    window_height = window_region[3] - window_region[1]

    # Calculate scaling factors based on the reference resolution
    scale_x = window_width / reference_resolution[0]
    scale_y = window_height / reference_resolution[1]

    # Use the smaller scaling factor to maintain aspect ratio
    scale_factor = min(scale_x, scale_y)

    # Resize the target image
    new_width = int(target_img.shape[1] * scale_factor)
    new_height = int(target_img.shape[0] * scale_factor)
    resized_img = cv2.resize(target_img, (new_width, new_height), interpolation=cv2.INTER_LINEAR)

    print(f"Resized target image to: {new_width}x{new_height}")
    return resized_img

# === MAIN LOOP ===

def main():
    window = find_game_window(GAME_WINDOW_TITLE)
    if window is None:
        print(f"Game window '{GAME_WINDOW_TITLE}' not found.")
        return

    # Get the absolute region of the game window
    window_region = get_window_region(window)
    print(f"Game window region: {window_region}")

    # Calculate the dimensions of the game window
    window_width = window_region[2] - window_region[0]
    window_height = window_region[3] - window_region[1]
    print(f"Game window size: {window_width}x{window_height}")

    # Define relative offsets for the search region (percentages of the window size)
    relative_offset = (0.4, 0.3, 0.2, 0.2)  # Example: 40% x, 30% y, 20% width, 20% height
    region = calculate_search_region(window_region, relative_offset)
    print(f"Dynamic search region: {region}")

    # Load the target image
    target_img = cv2.imread(TARGET_IMAGE_PATH, cv2.IMREAD_GRAYSCALE)
    if target_img is None:
        print("Failed to load target image.")
        return

    # Resize the target image based on the current window size
    reference_resolution = (2734, 1407)  # Replace with the resolution the target image was designed for
    target_img = resize_target_image(target_img, window_region, reference_resolution)

    show_debug = DEBUG_MODE
    debug_window_title = f"Debug Viewer - {GAME_WINDOW_TITLE} ({window_width}x{window_height})"
    already_clicked = False
    fish_count = 0

    while True:
        frame, fish_found, fish_pos = search_image_in_region(target_img, region, THRESHOLD)

        # When fish is detected and hasn't been clicked yet
        if fish_found and not already_clicked and fish_pos:
            # Adjust click position dynamically based on the fish position
            click_x = fish_pos[0]
            click_y = fish_pos[1] - 100 
            print(f"Right-clicking at offset position: ({click_x}, {click_y})")
            pyautogui.rightClick(click_x, click_y)
            fish_count += 1
            print(f"Fish/Items caught: {fish_count}")
            already_clicked = True

            # === Wait for fish icon to disappear ===
            while True:
                _, still_there, _ = search_image_in_region(target_img, region, THRESHOLD)
                if not still_there:
                    break
                time.sleep(0.2)  # Poll every 200ms

            # Cast the line again
            time.sleep(0.2)
            cast_fishing_line()

        # Reset click if image disappears
        if not fish_found:
            already_clicked = False

        # Show or hide debug window
        if show_debug:
            cv2.imshow(debug_window_title, frame)
        else:
            try:
                if cv2.getWindowProperty(debug_window_title, cv2.WND_PROP_VISIBLE) >= 0:
                    cv2.destroyWindow(debug_window_title)
            except cv2.error:
                pass

        # Handle keypresses
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Exiting loop.")
            break
        elif key == ord('d'):
            show_debug = not show_debug
            print(f"Debug window {'enabled' if show_debug else 'disabled'}.")

        time.sleep(LOOP_DELAY)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
