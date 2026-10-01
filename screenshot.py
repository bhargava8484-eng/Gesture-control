"""
screenshot.py

Captures timestamped screenshots using PyAutoGUI and stores them in the
screenshots/ folder.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import pyautogui


class ScreenshotManager:
    """Creates and saves screenshots with unique timestamp-based filenames."""

    def __init__(self, output_dir: str | Path | None = None) -> None:
        # Store captures beside this project even when the app is launched from
        # another working directory (for example, from a desktop shortcut).
        self.output_dir = Path(output_dir) if output_dir is not None else Path(__file__).resolve().parent / "screenshots"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def capture(self) -> Path:
        """Capture the current screen and save it as a PNG file."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = self.output_dir / f"screenshot_{timestamp}.png"
        image = pyautogui.screenshot()
        image.save(file_path)
        return file_path

    def capture_frame(self, frame) -> Path:
        """Save the annotated camera preview frame without capturing the desktop."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_path = self.output_dir / f"preview_{timestamp}.png"
        if not cv2.imwrite(str(file_path), frame):
            raise OSError(f"Could not save preview image to {file_path}")
        return file_path
