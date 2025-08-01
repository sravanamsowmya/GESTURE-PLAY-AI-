import cv2
import numpy as np
import random
import mediapipe as mp
import time

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7) # Added confidence parameters
mp_draw = mp.solutions.drawing_utils

size = 4
board = np.zeros((size, size), dtype=int)
score = 0
last_gesture_time = time.time()
gesture_delay = 1.0

def add_random_tile():
    empty = list(zip(*np.where(board == 0)))
    if empty:
        r, c = random.choice(empty)
        board[r][c] = 2 if random.random() < 0.9 else 4

def compress(line):
    global score
    new = [i for i in line if i != 0]
    merged = []
    skip = False
    for i in range(len(new)):
        if skip:
            skip = False
            continue
        if i + 1 < len(new) and new[i] == new[i + 1]:
            merged_val = new[i] * 2
            merged.append(merged_val)
            score += merged_val
            skip = True
        else:
            merged.append(new[i])
    return merged + [0] * (size - len(merged))

def move_left():
    global board
    moved = False
    new_board = []
    for row in board:
        compressed = compress(row)
        if not np.array_equal(row, compressed):
            moved = True
        new_board.append(compressed)
    if moved:
        board = np.array(new_board)
        add_random_tile()
    return moved

def move_right():
    global board
    moved = False
    new_board = []
    for row in board:
        reversed_row = row[::-1]
        compressed = compress(reversed_row)
        restored = compressed[::-1]
        if not np.array_equal(row, restored):
            moved = True
        new_board.append(restored)
    if moved:
        board = np.array(new_board)
        add_random_tile()
    return moved

def move_up():
    global board
    board = board.T
    moved = move_left()
    board = board.T
    return moved

def move_down():
    global board
    board = board.T
    moved = move_right()
    board = board.T
    return moved

def count_fingers(hand_landmarks):
    tips = [8, 12, 16, 20]
    fingers = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers += 1
    return fingers

def get_direction_from_fingers(fingers):
    if fingers == 1:
        return "up"
    elif fingers == 2:
        return "down"
    elif fingers == 3:
        return "left"
    elif fingers == 4:
        return "right"
    return "none"

def draw_board(board):
    tile_colors = {
        0: (50, 50, 50),
        2: (200, 200, 200),
        4: (170, 170, 170),
        8: (255, 180, 100),
        16: (255, 150, 80),
        32: (255, 100, 60),
        64: (255, 80, 30),
        128: (255, 60, 30),
        256: (255, 40, 30),
        512: (255, 20, 20),
        1024: (255, 0, 0),
        2048: (0, 255, 0)
    }

    cell_size = 150
    board_img = np.zeros((cell_size * size, cell_size * size, 3), dtype=np.uint8)

    for r in range(size):
        for c in range(size):
            val = board[r][c]
            color = tile_colors.get(val, (255, 255, 255))
            x1, y1 = c * cell_size, r * cell_size
            x2, y2 = x1 + cell_size, y1 + cell_size
            cv2.rectangle(board_img, (x1, y1), (x2, y2), color, -1)
            if val != 0:
                text_size = cv2.getTextSize(str(val), cv2.FONT_HERSHEY_SIMPLEX, 2, 4)[0]
                text_x = x1 + (cell_size - text_size[0]) // 2
                text_y = y1 + (cell_size + text_size[1]) // 2
                cv2.putText(board_img, str(val), (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 4)

    return board_img

def game_over():
    temp = board.copy()
    if move_up() or move_down() or move_left() or move_right():
        board[:] = temp
        return False
    board[:] = temp
    return True

add_random_tile()
add_random_tile()

cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width to 1280
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) # Set height to 720


while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    fingers = 0
    direction = "none"
    moved = False

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
            fingers = count_fingers(handLms)
            direction = get_direction_from_fingers(fingers)

    if 1 <= fingers <= 4 and time.time() - last_gesture_time > gesture_delay:
        if direction == "up":
            moved = move_up()
        elif direction == "down":
            moved = move_down()
        elif direction == "left":
            moved = move_left()
        elif direction == "right":
            moved = move_right()
        if moved:
            last_gesture_time = time.time()

    board_img = draw_board(board)
    board_img_resized = cv2.resize(board_img, (300, 300))
    frame_resized = cv2.resize(frame, (300, 300))

    combined = np.hstack([frame_resized, board_img_resized])

    cv2.putText(combined, f"Score: {score}", (10, 290), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    cv2.putText(combined, "1=Up 2=Down 3=Left 4=Right", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 255, 100), 1)
    if fingers == 0:
        cv2.putText(combined, "Fist detected: Waiting...", (10, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)

    if game_over():
        cv2.putText(combined, "Game Over!", (70, 150), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3)
        cv2.imshow("Gesture 2048", combined)
        cv2.waitKey(3000)
        board = np.zeros((size, size), dtype=int)
        add_random_tile()
        add_random_tile()
        score = 0
        last_gesture_time = time.time()

    cv2.imshow("Gesture 2048", combined)

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or cv2.getWindowProperty("Gesture 2048", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()