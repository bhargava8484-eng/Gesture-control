"""
gesture_controller.py

Contains reusable gesture-recognition logic and cooldown/debounce helpers.
Keeping this logic separate makes the main loop easier to read and explain
during a mini-project viva.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Dict, List

from hand_detector import Landmark


THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20

THUMB_MCP = 2
INDEX_PIP = 6
INDEX_MCP = 5
MIDDLE_PIP = 10
RING_PIP = 14
PINKY_PIP = 18
THUMB_IP = 3


@dataclass
class GestureState:
    """Result object returned after analyzing the current hand pose."""

    name: str
    fingers: Dict[str, bool]
    distances: Dict[str, float]


class GestureController:
    """Recognizes gestures from MediaPipe landmarks and prevents repeated triggers."""

    def __init__(self, touch_threshold_ratio: float = 0.32, action_cooldown: float = 0.75) -> None:
        self.touch_threshold_ratio = touch_threshold_ratio
        self.action_cooldown = action_cooldown
        self.last_action_time: Dict[str, float] = {}
        self.previous_gesture = "NONE"

    @staticmethod
    def distance(point_a: Landmark, point_b: Landmark) -> float:
        """Calculate Euclidean distance between two landmarks in pixel space."""

        return math.hypot(point_a.x - point_b.x, point_a.y - point_b.y)

    def can_trigger(self, action_name: str) -> bool:
        """
        Return True only if the action has waited long enough since last trigger.

        This avoids repeated clicking or repeated screenshots while a gesture is
        held in front of the camera.
        """

        current_time = time.monotonic()
        last_time = self.last_action_time.get(action_name, 0.0)
        if current_time - last_time >= self.action_cooldown:
            self.last_action_time[action_name] = current_time
            return True
        return False

    def is_new_gesture(self, gesture_name: str) -> bool:
        """Return True when the current gesture is different from the previous frame."""

        is_new = gesture_name != self.previous_gesture
        self.previous_gesture = gesture_name
        return is_new

    def fingers_up(self, landmarks: List[Landmark], hand_label: str | None = None) -> Dict[str, bool]:
        """
        Determine which fingers are raised.

        For four fingers, the fingertip is considered raised when it is above
        the PIP joint in image coordinates. For the thumb, horizontal movement is
        used because the thumb points sideways more often than upward.
        """

        if len(landmarks) < 21:
            return {
                "thumb": False,
                "index": False,
                "middle": False,
                "ring": False,
                "pinky": False,
            }

        # Thumb direction changes with left/right hand and mirrored camera feeds.
        # A distance-based check is more reliable for an open-palm screenshot
        # gesture: the thumb tip should be farther from the palm/index base than
        # the thumb's inner joints are.
        thumb_tip_distance = self.distance(landmarks[THUMB_TIP], landmarks[INDEX_MCP])
        thumb_ip_distance = self.distance(landmarks[THUMB_IP], landmarks[INDEX_MCP])
        thumb_mcp_distance = self.distance(landmarks[THUMB_MCP], landmarks[INDEX_MCP])
        thumb_up = thumb_tip_distance > max(thumb_ip_distance, thumb_mcp_distance) * 1.15

        return {
            "thumb": thumb_up,
            "index": landmarks[INDEX_TIP].y < landmarks[INDEX_PIP].y,
            "middle": landmarks[MIDDLE_TIP].y < landmarks[MIDDLE_PIP].y,
            "ring": landmarks[RING_TIP].y < landmarks[RING_PIP].y,
            "pinky": landmarks[PINKY_TIP].y < landmarks[PINKY_PIP].y,
        }

    def analyze(self, landmarks: List[Landmark], hand_label: str | None = None) -> GestureState:
        """
        Convert landmarks into a high-level gesture name.

        Priority matters: touch gestures are checked before finger-count gestures
        so clicks and drag are not accidentally interpreted as media controls.
        """

        if len(landmarks) < 21:
            self.previous_gesture = "NONE"
            return GestureState("NONE", {}, {})

        fingers = self.fingers_up(landmarks, hand_label)
        distances = {
            "thumb_index": self.distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP]),
            "thumb_middle": self.distance(landmarks[THUMB_TIP], landmarks[MIDDLE_TIP]),
            "index_middle": self.distance(landmarks[INDEX_TIP], landmarks[MIDDLE_TIP]),
            "thumb_ring": self.distance(landmarks[THUMB_TIP], landmarks[RING_TIP]),
        }

        # Scale the pinch threshold to the detected hand. A fixed pixel value
        # becomes unreliable when the user moves closer to or farther from the
        # camera, especially during a live presentation.
        palm_width = self.distance(landmarks[INDEX_MCP], landmarks[17])
        touch_threshold = max(18.0, min(58.0, palm_width * self.touch_threshold_ratio))
        thumb_index_touch = distances["thumb_index"] < touch_threshold
        thumb_middle_touch = distances["thumb_middle"] < touch_threshold
        index_middle_touch = distances["index_middle"] < touch_threshold
        thumb_ring_touch = distances["thumb_ring"] < touch_threshold

        if thumb_ring_touch:
            gesture = "DRAG"
        elif thumb_middle_touch:
            gesture = "RIGHT CLICK"
        elif index_middle_touch:
            gesture = "DOUBLE CLICK"
        elif thumb_index_touch:
            gesture = "LEFT CLICK"
        elif all(fingers.values()):
            gesture = "SCREENSHOT"
        elif fingers["thumb"] and not any(
            fingers[name] for name in ("index", "middle", "ring", "pinky")
        ):
            gesture = "RECORD"
        elif fingers["index"] and fingers["middle"] and fingers["ring"] and fingers["pinky"]:
            gesture = "PREVIOUS TRACK"
        elif fingers["index"] and fingers["middle"] and fingers["ring"] and not fingers["pinky"]:
            gesture = "NEXT TRACK"
        elif fingers["index"] and fingers["middle"] and not fingers["ring"] and not fingers["pinky"]:
            gesture = "PLAY/PAUSE"
        elif fingers["thumb"] and fingers["index"] and not fingers["middle"]:
            gesture = "VOLUME CONTROL"
        elif fingers["index"]:
            gesture = "MOUSE MOVE"
        else:
            gesture = "NONE"

        return GestureState(gesture, fingers, distances)
