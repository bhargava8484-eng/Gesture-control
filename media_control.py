"""
media_control.py

Provides keyboard media controls through PyAutoGUI.
"""

from __future__ import annotations

import pyautogui


class MediaControl:
    """Sends media key presses to the operating system."""

    def play_pause(self) -> None:
        pyautogui.press("playpause")

    def next_track(self) -> None:
        pyautogui.press("nexttrack")

    def previous_track(self) -> None:
        pyautogui.press("prevtrack")
