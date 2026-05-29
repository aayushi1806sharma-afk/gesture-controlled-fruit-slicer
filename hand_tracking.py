import cv2
import mediapipe as mp


class HandTracker:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

        self.mp_draw = mp.solutions.drawing_utils

    def detect_hand(self, frame):
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb_frame)

        finger_position = None

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:

                # Draw hand landmarks
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS
                )

                # Index fingertip landmark = 8
                h, w, c = frame.shape

                fingertip = hand_landmarks.landmark[8]

                cx = int(fingertip.x * w)
                cy = int(fingertip.y * h)

                finger_position = (cx, cy)

                # Draw fingertip circle
                cv2.circle(frame, finger_position, 15, (0, 255, 0), -1)

        return frame, finger_position