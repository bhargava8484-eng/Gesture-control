"""
mouse_control.py

Maps hand landmark positions to desktop mouse operations using PyAutoGUI.
"""

from __future__ import annotations

from typing import Tuple

import numpy as np
import pyautogui

from hand_detector import Landmark


class MouseControl:
    """Controls cursor movement, clicking, and drag/drop."""

    def __init__(self, frame_reduction: int = 80, smoothing: float = 5.0) -> None:
        pyautogui.FAILSAFE = True
        self.screen_width, self.screen_height = pyautogui.size()
        self.frame_reduction = frame_reduction
        self.smoothing = smoothing
        self.previous_x = None
        self.previous_y = None
        self.dragging = False

    def move_cursor(self, index_tip: Landmark, frame_size: Tuple[int, int]) -> None:
        """
        Move cursor according to index fingertip position.

        A reduced inner frame is used so the cursor can reach screen edges more
        comfortably even when the finger does not touch the camera frame border.
        """

        frame_width, frame_height = frame_size
        margin_x = min(self.frame_reduction, frame_width // 4)
        margin_y = min(self.frame_reduction, frame_height // 4)
        x = np.interp(
            index_tip.x,
            (margin_x, frame_width - margin_x),
            (0, self.screen_width),
        )
        y = np.interp(
            index_tip.y,
            (margin_y, frame_height - margin_y),
            (0, self.screen_height),
        )

        # Start at the detected finger position instead of sweeping the pointer
        # from the top-left corner on the first frame.
        if self.previous_x is None or self.previous_y is None:
            current_x, current_y = x, y
        else:
            smoothing = max(1.0, self.smoothing)
            current_x = self.previous_x + (x - self.previous_x) / smoothing
            current_y = self.previous_y + (y - self.previous_y) / smoothing

        pyautogui.moveTo(current_x, current_y)
        self.previous_x = current_x
        self.previous_y = current_y

    def left_click(self) -> None:
        pyautogui.click(button="left")

    def right_click(self) -> None:
        pyautogui.click(button="right")

    def double_click(self) -> None:
        pyautogui.doubleClick()

    def start_drag(self) -> None:
        if not self.dragging:
            pyautogui.mouseDown(button="left")
            self.dragging = True

    def stop_drag(self) -> None:
        if self.dragging:
            pyautogui.mouseUp(button="left")
            self.dragging = False
