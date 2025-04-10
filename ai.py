import cv2
import mediapipe as mp
import pyautogui
import time
import sys

# Initialize webcam
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open webcam.")
    sys.exit()

# Initialize Mediapipe Hand Tracking
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.6)

# Get screen size
screen_width, screen_height = pyautogui.size()

# Track hand position for click detection
last_x, last_y = None, None
still_time = 0
scroll_mode = False
tab_switch_mode = False
mode_start_time = 0

# Finger state tracking
prev_thumb_tip = None
prev_index_tip = None

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb_frame)

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
                index_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
                middle_tip = hand_landmarks.landmark[mp_hands.HandLandmark.MIDDLE_FINGER_TIP]

                index_x = int(index_tip.x * w)
                index_y = int(index_tip.y * h)
                thumb_x = int(thumb_tip.x * w)
                thumb_y = int(thumb_tip.y * h)
                middle_x = int(middle_tip.x * w)
                middle_y = int(middle_tip.y * h)

                # ✅ Fixed distance calculation
                thumb_index_dist = (((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2) ** 0.5)
                index_middle_dist = (((index_x - middle_x) ** 2 + (index_y - middle_y) ** 2) ** 0.5)

                mouse_x = int((index_x / w) * screen_width)
                mouse_y = int((index_y / h) * screen_height)

                current_time = time.time()

                # Scroll mode
                if thumb_index_dist < 30:
                    if not scroll_mode:
                        scroll_mode = True
                        mode_start_time = current_time

                    if scroll_mode and (current_time - mode_start_time) > 0.5:
                        if prev_index_tip is not None:
                            vertical_move = index_tip.y - prev_index_tip.y
                            scroll_amount = int(vertical_move * 1000)
                            pyautogui.scroll(scroll_amount)
                else:
                    scroll_mode = False

                # Tab switch mode
                if index_middle_dist < 30:
                    if not tab_switch_mode:
                        tab_switch_mode = True
                        mode_start_time = current_time

                    if tab_switch_mode and (current_time - mode_start_time) > 0.5:
                        if prev_index_tip is not None:
                            horizontal_move = index_tip.x - prev_index_tip.x
                            if horizontal_move > 0.02:
                                pyautogui.hotkey('ctrl', 'tab')
                                time.sleep(0.2)
                            elif horizontal_move < -0.02:
                                pyautogui.hotkey('ctrl', 'shift', 'tab')
                                time.sleep(0.2)
                else:
                    tab_switch_mode = False

                # Normal movement
                if not scroll_mode and not tab_switch_mode:
                    pyautogui.moveTo(mouse_x, mouse_y, duration=0.1)

                    if last_x is not None and last_y is not None:
                        if abs(index_x - last_x) < 10 and abs(index_y - last_y) < 10:
                            still_time += 1
                            if still_time == 20:
                                pyautogui.click()
                            elif still_time == 40:
                                pyautogui.rightClick()
                        else:
                            still_time = 0

                last_x, last_y = index_x, index_y
                prev_thumb_tip = thumb_tip
                prev_index_tip = index_tip

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\nExiting program...")
finally:
    cap.release()
    cv2.destroyAllWindows()
