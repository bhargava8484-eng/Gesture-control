"""
hand_detector.py

Wraps MediaPipe Hands in an object-oriented interface. The classic Solutions
API is used because it bundles the hand tracking graphs and model assets.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import mediapipe as mp


@dataclass
class Landmark:
    """One hand landmark in pixel and normalized image coordinates."""

    id: int
    x: int
    y: int
    z: float
    normalized_x: float
    normalized_y: float


class HandDetector:
    """Detect and draw one or more hands from OpenCV BGR video frames."""

    def __init__(
        self,
        static_image_mode: bool = False,
        max_num_hands: int = 1,
        model_complexity: int = 1,
        min_detection_confidence: float = 0.7,
        min_tracking_confidence: float = 0.7,
    ) -> None:
        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils
        self.hands = self.mp_hands.Hands(
            static_image_mode=static_image_mode,
            max_num_hands=max_num_hands,
            model_complexity=model_complexity,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self.results = None
        self.hand_label: Optional[str] = None

    def find_hands(self, frame, draw: bool = True):
        """Detect hands in a BGR frame and optionally draw the landmark graph."""

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(rgb_frame)
        self.hand_label = None

        if self.results.multi_handedness:
            self.hand_label = self.results.multi_handedness[0].classification[0].label

        if draw and self.results.multi_hand_landmarks:
            for hand_landmarks in self.results.multi_hand_landmarks:
                self.mp_draw.draw_landmarks(
                    frame,
                    hand_landmarks,
                    self.mp_hands.HAND_CONNECTIONS,
                )

        return frame

    @staticmethod
    def _to_pixel(normalized_x: float, normalized_y: float, width: int, height: int) -> Tuple[int, int]:
        x = max(0, min(width - 1, int(normalized_x * width)))
        y = max(0, min(height - 1, int(normalized_y * height)))
        return x, y

    def get_landmarks(self, frame) -> List[Landmark]:
        """Return the first detected hand as frame pixel coordinates."""

        landmarks: List[Landmark] = []
        if not self.results or not self.results.multi_hand_landmarks:
            return landmarks

        height, width = frame.shape[:2]
        hand_landmarks = self.results.multi_hand_landmarks[0]

        for landmark_id, landmark in enumerate(hand_landmarks.landmark):
            pixel_x, pixel_y = self._to_pixel(landmark.x, landmark.y, width, height)
            landmarks.append(
                Landmark(
                    id=landmark_id,
                    x=pixel_x,
                    y=pixel_y,
                    z=landmark.z,
                    normalized_x=landmark.x,
                    normalized_y=landmark.y,
                )
            )

        return landmarks

    def get_bounding_box(self, landmarks: List[Landmark]) -> Optional[Tuple[int, int, int, int]]:
        """Return the hand bounds as x_min, y_min, x_max, y_max."""

        if not landmarks:
            return None

        x_values = [landmark.x for landmark in landmarks]
        y_values = [landmark.y for landmark in landmarks]
        return min(x_values), min(y_values), max(x_values), max(y_values)

    def close(self) -> None:
        """Release the MediaPipe graph resources."""

        self.hands.close()
