import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import numpy as np

class HandTracker:
    # Legacy HAND_CONNECTIONS for drawing
    HAND_CONNECTIONS = [
        (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
        (5, 6), (6, 7), (7, 8),               # Index
        (9, 10), (10, 11), (11, 12),         # Middle
        (13, 14), (14, 15), (15, 16),        # Ring
        (17, 18), (18, 19), (19, 20),        # Pinky
        (0, 5), (5, 9), (9, 13), (13, 17), (0, 17) # Palm
    ]

    def __init__(self, mode=False, max_hands=2, detection_con=0.7, track_con=0.7):
        base_options = python.BaseOptions(model_asset_path='hand_landmarker.task')
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.detector = vision.HandLandmarker.create_from_options(options)
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=True):
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        
        # Detect
        detection_result = self.detector.detect(mp_image)
        
        hands_data = []
        if detection_result.hand_landmarks:
            h, w, c = img.shape
            for hand_lms in detection_result.hand_landmarks:
                lm_list = []
                for id, lm in enumerate(hand_lms):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append({'id': id, 'x': cx, 'y': cy, 'raw_x': lm.x, 'raw_y': lm.y})
                hands_data.append(lm_list)
                
                if draw:
                    # Draw landmarks manually since solutions is missing
                    for conn in self.HAND_CONNECTIONS:
                        p1 = lm_list[conn[0]]
                        p2 = lm_list[conn[1]]
                        cv2.line(img, (p1['x'], p1['y']), (p2['x'], p2['y']), (0, 255, 0), 2)
                    for pt in lm_list:
                        cv2.circle(img, (pt['x'], pt['y']), 5, (255, 0, 0), -1)
        
        return img, hands_data

    @staticmethod
    def get_distance(p1, p2):
        return np.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])

    def get_fingers_up(self, hand):
        fingers = []
        # Thumb
        if hand[self.tip_ids[0]]['x'] > hand[self.tip_ids[0] - 1]['x']:
            fingers.append(1)
        else:
            fingers.append(0)

        # 4 Fingers
        for id in range(1, 5):
            if hand[self.tip_ids[id]]['y'] < hand[self.tip_ids[id] - 2]['y']:
                fingers.append(1)
            else:
                fingers.append(0)
        return fingers

