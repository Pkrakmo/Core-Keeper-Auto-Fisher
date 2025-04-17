import pyautogui
import pygetwindow as gw
import cv2
import numpy as np
from PIL import ImageGrab
import time

GAME_WINDOW_TITLE = "Core Keeper"              # Game window title
TARGET_IMAGE_PATH = "icon.png"                # Path to fish icon image
SEARCH_REGION_OFFSET = (1200, 450, 300, 300)  # Relative region (x, y, width, height)
LOOP_DELAY = 1.0                               # Delay between each loop
THRESHOLD = 0.8                                # Confidence threshold for image matching
DEBUG_MODE = False                             # Toggle debug view with 'd' key

def find_game_window(title):
    """Find the game window by its title."""
    windows = gw.getWindowsWithTitle(title)
    return windows[0] if windows else None

def get_window_region(window, offset):
    """Get absolute screen region based on window position and offset."""
    x = window.left + offset[0]
    y = window.top + offset[1]
    width = offset[2]
    height = offset[3]
    return (x, y, x + width, y + height)

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

# === MAIN LOOP ===

def main():
    window = find_game_window(GAME_WINDOW_TITLE)
    if window is None:
        print(f"Game window '{GAME_WINDOW_TITLE}' not found.")
        return

    region = get_window_region(window, SEARCH_REGION_OFFSET)
    print(f"Searching in region: {region}")

    target_img = cv2.imread(TARGET_IMAGE_PATH, cv2.IMREAD_GRAYSCALE)
    if target_img is None:
        print("Failed to load target image.")
        return

    show_debug = DEBUG_MODE
    already_clicked = False

    while True:
        frame, fish_found, fish_pos = search_image_in_region(target_img, region, THRESHOLD)

        # When fish is detected and hasn't been clicked yet
        if fish_found and not already_clicked and fish_pos:
            # Offset the click 100 pixels to the left of the fish icon
            click_x = fish_pos[0] - 100
            click_y = fish_pos[1]
            print(f"Right-clicking at offset position: ({click_x}, {click_y})")
            pyautogui.rightClick(click_x, click_y)
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
            cv2.imshow("Debug Viewer", frame)
        else:
            try:
                if cv2.getWindowProperty("Debug Viewer", cv2.WND_PROP_VISIBLE) >= 0:
                    cv2.destroyWindow("Debug Viewer")
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
