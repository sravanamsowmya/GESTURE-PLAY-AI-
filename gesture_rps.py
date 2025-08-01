import cv2
import random
import mediapipe as mp
import time

# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7) # Added confidence parameters
mp_draw = mp.solutions.drawing_utils

# Game State
choices = ["rock", "paper", "scissors"]
player_score = 0
computer_score = 0

# Timing control
last_move_time = time.time()
delay_between_moves = 2  # seconds

# Gesture Detection Logic
def detect_gesture(hand_landmarks):
    tips = [8, 12, 16, 20]
    fingers = []
    for tip in tips:
        if hand_landmarks.landmark[tip].y < hand_landmarks.landmark[tip - 2].y:
            fingers.append(1)
        else:
            fingers.append(0)

    if sum(fingers) == 0:
        return "rock"
    elif sum(fingers) == 4:
        return "paper"
    elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0:
        return "scissors"
    return "none"

# Game Logic
def get_result(player, computer):
    global player_score, computer_score
    if player == computer:
        return "Draw"
    elif (player == "rock" and computer == "scissors") or \
         (player == "paper" and computer == "rock") or \
         (player == "scissors" and computer == "paper"):
        player_score += 1
        return "You Win"
    else:
        computer_score += 1
        return "Computer Wins"

# Start Webcam
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # Set width to 1280
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720) # Set height to 720

# Initial values
player_move = "none"
computer_move = "none"
result_text = "Show hand gesture!"

while True:
    success, frame = cap.read()
    if not success:
        break

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = hands.process(rgb_frame)

    current_time = time.time()

    if result.multi_hand_landmarks:
        for handLms in result.multi_hand_landmarks:
            mp_draw.draw_landmarks(frame, handLms, mp_hands.HAND_CONNECTIONS)
            detected_move = detect_gesture(handLms)

            # Process only if cooldown has passed
            if detected_move in choices and (current_time - last_move_time > delay_between_moves):
                player_move = detected_move
                computer_move = random.choice(choices)
                result_text = get_result(player_move, computer_move)
                last_move_time = current_time

    # Display Results
    cv2.putText(frame, f"Your Move: {player_move}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0,255,0), 2)
    cv2.putText(frame, f"Computer: {computer_move}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255,0,0), 2)
    cv2.putText(frame, f"Result: {result_text}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2)
    cv2.putText(frame, f"Score You: {player_score} | CPU: {computer_score}", (10, 140), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255,255,0), 2)

    cv2.imshow("Rock Paper Scissors - Gesture Mode", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or cv2.getWindowProperty("Rock Paper Scissors - Gesture Mode", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()