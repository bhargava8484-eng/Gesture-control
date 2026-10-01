"""
volume_control.py

Cross-platform volume control. On Windows this uses Pycaw; on macOS it
falls back to `osascript` to set the system output volume. If neither is
available the class disables volume control gracefully.
"""

from __future__ import annotations

from typing import Tuple
import platform
import subprocess
import time

import numpy as np

# Attempt to import Pycaw (Windows). If unavailable, we'll fall back to
# macOS `osascript` based implementation at runtime.
_HAS_PYCAW = False
try:
    from comtypes import CLSCTX_ALL  # type: ignore
    from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore

    _HAS_PYCAW = True
except Exception:
    _HAS_PYCAW = False


class VolumeControl:
    """Handles system volume in a cross-platform way.

    - On Windows: uses Pycaw if available.
    - On macOS: uses `osascript` to set `output volume`.
    - Otherwise: disabled (no-op).
    """

    def __init__(self, min_hand_distance: float = 25.0, max_hand_distance: float = 220.0) -> None:
        self.min_hand_distance = min_hand_distance
        self.max_hand_distance = max_hand_distance
        self.volume = None
        self.min_volume = -65.25
        self.max_volume = 0.0
        self.is_available = False
        self._platform = platform.system()
        self._last_set_time = 0.0
        self._last_volume_percent = None

        if self._platform == "Windows" and _HAS_PYCAW:
            try:
                self._initialize_audio_endpoint()
                self.is_available = True
            except Exception as error:
                print(f"Volume control disabled (pycaw init failed): {error}")
                self.is_available = False
        elif self._platform == "Darwin":
            # macOS: osascript should be available on the system PATH.
            # We'll treat this as available; actual calls may still fail.
            self.is_available = True
        else:
            print(f"Volume control disabled: unsupported platform {self._platform}")

    def _initialize_audio_endpoint(self) -> None:
        """Initialize the Windows audio endpoint used by Pycaw."""

        devices = AudioUtilities.GetSpeakers()

        if hasattr(devices, "EndpointVolume"):
            self.volume = devices.EndpointVolume
        else:
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self.volume = interface.QueryInterface(IAudioEndpointVolume)

        self.min_volume, self.max_volume, _ = self.volume.GetVolumeRange()

    def _set_macos_volume_percent(self, percent: int) -> None:
        """Set macOS system output volume using AppleScript (osascript)."""

        # Clamp to [0, 100]
        percent = max(0, min(100, int(percent)))
        try:
            subprocess.run(
                ["osascript", "-e", f"set volume output volume {percent}"],
                check=True,
                timeout=1.0,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as error:
            print(f"Failed to set macOS volume: {error}")

    def set_volume_by_distance(self, distance: float) -> Tuple[int, float]:
        """
        Convert hand distance to system volume.

        Returns volume percentage and a normalized scalar (0.0 - 1.0) for UI display.
        """

        volume_scalar = float(
            np.interp(
                distance,
                (self.min_hand_distance, self.max_hand_distance),
                (0.0, 1.0),
            )
        )
        volume_scalar = float(np.clip(volume_scalar, 0.0, 1.0))
        volume_percent = int(volume_scalar * 100)
        volume_percent = int(np.clip(volume_percent, 0, 100))

        # AppleScript launches a new process. Limit updates so volume gestures
        # remain responsive without spawning a process on every camera frame.
        current_time = time.monotonic()
        should_update = (
            self._last_volume_percent is None
            or abs(volume_percent - self._last_volume_percent) >= 2
        ) and current_time - self._last_set_time >= 0.18

        if not should_update:
            return volume_percent, volume_scalar

        if self._platform == "Windows" and _HAS_PYCAW and self.volume is not None:
            try:
                # Pycaw accepts a scalar between 0.0 and 1.0
                self.volume.SetMasterVolumeLevelScalar(volume_scalar, None)
            except Exception as error:
                print(f"Failed to set Windows volume: {error}")
        elif self._platform == "Darwin":
            self._set_macos_volume_percent(volume_percent)

        self._last_set_time = current_time
        self._last_volume_percent = volume_percent

        return volume_percent, volume_scalar
