"""Record the annotated camera preview for a project demonstration."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import cv2


class SessionRecorder:
    """Save the live camera dashboard as a local MP4 video."""

    def __init__(self, output_dir: str | Path | None = None, fps: float = 24.0) -> None:
        self.output_dir = (
            Path(output_dir)
            if output_dir is not None
            else Path(__file__).resolve().parent / "recordings"
        )
        self.fps = fps
        self.writer: Optional[cv2.VideoWriter] = None
        self.file_path: Optional[Path] = None

    @property
    def is_recording(self) -> bool:
        """Whether a video file is currently being written."""

        return self.writer is not None

    def start(self, frame) -> Path:
        """Start a new MP4 recording using the current preview dimensions."""

        if self.is_recording:
            raise RuntimeError("A recording is already in progress")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        file_path = self.output_dir / f"gesture_session_{timestamp}.mp4"
        height, width = frame.shape[:2]
        writer = cv2.VideoWriter(
            str(file_path),
            cv2.VideoWriter_fourcc(*"mp4v"),
            self.fps,
            (width, height),
        )
        if not writer.isOpened():
            writer.release()
            raise RuntimeError("This OpenCV build could not start MP4 recording")

        self.writer = writer
        self.file_path = file_path
        return file_path

    def write(self, frame) -> None:
        """Append one annotated preview frame when recording is active."""

        if self.writer is not None:
            self.writer.write(frame)

    def stop(self) -> Optional[Path]:
        """Finish the current video and return its saved path, if any."""

        if self.writer is None:
            return None

        self.writer.release()
        self.writer = None
        saved_path = self.file_path
        self.file_path = None
        return saved_path
