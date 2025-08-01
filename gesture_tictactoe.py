import cv2
import numpy as np
import mediapipe as mp
import time

# Initialize MediaPipe
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7) # Added confidence parameters
mp_draw = mp.solutions.drawing_utils

# Game board
board = [["" for _ in range(3)] for _ in range(3)]
player = "X"
cursor = [1, 1]  # Initial cursor
last_action_time = time.time()
delay = 1.0 

# Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width to 1280
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) # Set height to 720


def check_winner():
    lines = board + [list(col) for col in zip(*board)]
    lines.append([board[i][i] for i in range(3)])
    lines.append([board[i][2 - i] for i in range(3)])
    for line in lines:
        if line.count(line[0]) == 3 and line[0] != "":
            return line[0]
    return None

def check_draw():
    return all(cell != "" for row in board for cell in row)

def detect_fist_or_open(hand_landmarks):
    # Count extended fingers
    tips = [8, 12, 16, 20]
    extended = 0
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            extended += 1
    if extended >= 3: # Assuming 3 or more extended fingers for "open"
        return "open"
    else:
        return "fist"

def get_cell_from_position(x, y, width, height):
    col = min(2, int(3 * x / width))
    row = min(2, int(3 * y / height))
    return [row, col]

def draw_board(frame, cursor_row, cursor_col):
    h, w, _ = frame.shape
    cell_w = w // 3
    cell_h = h // 3

    # Grid lines
    for i in range(1, 3):
        cv2.line(frame, (0, i * cell_h), (w, i * cell_h), (255, 255, 255), 2)
        cv2.line(frame, (i * cell_w, 0), (i * cell_w, h), (255, 255, 255), 2)

    # X/O
    for r in range(3):
        for c in range(3):
            symbol = board[r][c]
            if symbol:
                x = c * cell_w + cell_w // 2
                y = r * cell_h + cell_h // 2
                cv2.putText(frame, symbol, (x - 20, y + 20), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 255, 0), 3)

    # Cursor highlight
    x1 = cursor_col * cell_w
    y1 = cursor_row * cell_h
    x2 = x1 + cell_w
    y2 = y1 + cell_h
    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 255), 3)

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame = cv2.flip(frame, 1)
    h, w, _ = frame.shape #
    gesture = "none"

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb)

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)

            gesture = detect_fist_or_open(handLms)

            # Get index finger tip to locate position
            index_tip = handLms.landmark[8]
            cx, cy = int(index_tip.x * w), int(index_tip.y * h)
            cursor = get_cell_from_position(cx, cy, w, h)

            # If gesture is "fist", place X
            if gesture == "fist" and time.time() - last_action_time > delay:
                row, col = cursor
                if board[row][col] == "":
                    board[row][col] = player
                    winner = check_winner()
                    if winner:
                        cv2.putText(frame, f"{winner} Wins!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                        cv2.imshow("Gesture Tic Tac Toe", frame)
                        cv2.waitKey(3000)
                        board = [["" for _ in range(3)] for _ in range(3)]
                        player = "X"
                        continue
                    elif check_draw():
                        cv2.putText(frame, "It's a Draw!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
                        cv2.imshow("Gesture Tic Tac Toe", frame)
                        cv2.waitKey(3000)
                        board = [["" for _ in range(3)] for _ in range(3)]
                        player = "X"
                        continue

                    # Computer move (first empty)
                    player = "O"
                    moved = False
                    for r in range(3):
                        for c in range(3):
                            if board[r][c] == "":
                                board[r][c] = "O"
                                moved = True
                                break
                        if moved:
                            break
                    winner = check_winner()
                    if winner:
                        cv2.putText(frame, f"{winner} Wins!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 3)
                        cv2.imshow("Gesture Tic Tac Toe", frame)
                        cv2.waitKey(3000)
                        board = [["" for _ in range(3)] for _ in range(3)]
                    elif check_draw():
                        cv2.putText(frame, "It's a Draw!", (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, (255, 255, 0), 3)
                        cv2.imshow("Gesture Tic Tac Toe", frame)
                        cv2.waitKey(3000)
                        board = [["" for _ in range(3)] for _ in range(3)]
                    player = "X"
                    last_action_time = time.time()

    draw_board(frame, cursor[0], cursor[1])
    cv2.putText(frame, f"Show ✋ to Move | ✊ to Place {player}", (10, h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 255, 0), 2)
    cv2.imshow("Gesture Tic Tac Toe", frame)

    key = cv2.waitKey(10) & 0xFF
    if key == ord('q') or cv2.getWindowProperty("Gesture Tic Tac Toe", cv2.WND_PROP_VISIBLE) < 1:
        break
cap.release()
cv2.destroyAllWindows()