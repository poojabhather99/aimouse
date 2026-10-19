"""Thin wrapper around MediaPipe Hands."""
from __future__ import annotations

import cv2
import mediapipe as mp


class HandDetector:
    def __init__(self, max_hands: int = 1, detection_conf: float = 0.5, tracking_conf: float = 0.5):
        self._hands_module = mp.solutions.hands
        self._hands = self._hands_module.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )
        self._draw = mp.solutions.drawing_utils
        self._results = None

    def find_hands(self, img, draw: bool = True):
        self._results = self._hands.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        if draw and self._results.multi_hand_landmarks:
            for hand in self._results.multi_hand_landmarks:
                self._draw.draw_landmarks(img, hand, self._hands_module.HAND_CONNECTIONS)
        return img

    def find_position(self, img, hand_no: int = 0):
        """Return ([[id, x, y], ...], bbox) in pixel coordinates; empty if no hand."""
        if not self._results or not self._results.multi_hand_landmarks:
            return [], ()
        h, w, _ = img.shape
        hand = self._results.multi_hand_landmarks[hand_no]
        lm = [[i, int(p.x * w), int(p.y * h)] for i, p in enumerate(hand.landmark)]
        xs, ys = [p[1] for p in lm], [p[2] for p in lm]
        return lm, (min(xs), min(ys), max(xs), max(ys))
