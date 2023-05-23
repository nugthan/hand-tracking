import cv2
import mediapipe as mp
import math

from pythonosc import udp_client

# ////// CHANGE ME ///////
cap = cv2.VideoCapture(2)

mpHands = mp.solutions.hands
hands = mpHands.Hands(
    max_num_hands=1,
)
mpDraw = mp.solutions.drawing_utils

# Rate limiter
prev_input = None
prev_note = None


def on_input_change(input_value):
    global prev_input

    if prev_input is None:
        prev_input = input_value
        return

    if input_value != prev_input:
        client.send_message('/indexplay', input_value)
        if input_value == 0:
            client.send_message('/C4', 0)
            client.send_message('/A#3', 0)
            client.send_message('/G#3', 0)
            client.send_message('/G3', 0)
        prev_input = input_value


def on_note_change(input_value):
    global prev_note
    global prev_input

    if prev_note is None:
        prev_note = input_value
        return

    if prev_input == 0:
        return
    if input_value != prev_note:
        if 36 < input_value < 39:
            client.send_message('/C4', 1)
            client.send_message('/A#3', 0)
            client.send_message('/G#3', 0)
            client.send_message('/G3', 0)
        elif 39 < input_value < 42:
            client.send_message('/A#3', 1)
            client.send_message('/C4', 0)
            client.send_message('/G#3', 0)
            client.send_message('/G3', 0)
        elif 42 < input_value < 45:
            client.send_message('/G#3', 1)
            client.send_message('/C4', 0)
            client.send_message('/A#3', 0)
            client.send_message('/G3', 0)
        elif 45 < input_value < 48:
            client.send_message('/G3', 1)
            client.send_message('/C4', 0)
            client.send_message('/A#3', 0)
            client.send_message('/G#3', 0)
        prev_note = input_value


# OSC SETUP

client = udp_client.SimpleUDPClient('127.0.0.1', 8000)

while True:
    success, image = cap.read()
    image = cv2.flip(image, 1)
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(imageRGB)
    # checking whether a hand is detected
    if results.multi_hand_landmarks:
        for landmarks in results.multi_hand_landmarks:  # working with each hand
            for id, lm in enumerate(landmarks.landmark):
                h, w, c = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                if id == 8:
                    cv2.circle(image, (cx, cy), 25, (0, 0, 255), cv2.FILLED)
                    client.send_message('/indexfingerx', cx / 6)

                    note = math.floor((cy - 0) / (700 - 0) * (47 - 57) + 47)
                    on_note_change(note)

                # detect if fingers are open
                if id == 4:
                    if lm.y < landmarks.landmark[3].y:
                        on_input_change(1)
                    else:
                        on_input_change(0)
                # distance between thumb and index finger
                if id == 8:
                    dist = ((landmarks.landmark[4].x - landmarks.landmark[8].x) ** 2 + (
                            landmarks.landmark[4].y - landmarks.landmark[8].y) ** 2) ** 0.5
                    client.send_message('/thumbfingerdistance', dist * 5)

            mpDraw.draw_landmarks(image, landmarks, mpHands.HAND_CONNECTIONS)
    cv2.imshow("Output", image)
    cv2.waitKey(1)
