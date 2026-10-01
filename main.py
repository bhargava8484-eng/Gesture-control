"""
Live entry point for the AI-Based Gesture Controlled Desktop Assistant.

The app captures a webcam frame, finds hand landmarks with MediaPipe, maps a
recognized pose to a desktop action, and renders a presentation-ready HUD.
"""

from __future__ import annotations

import argparse
import platform
import time
from pathlib import Path
from typing import Optional

import cv2

from gesture_controller import GestureController, INDEX_TIP
from hand_detector import HandDetector, Landmark
from media_control import MediaControl
from mouse_control import MouseControl
from screenshot import ScreenshotManager
from session_recorder import SessionRecorder
from volume_control import VolumeControl


WINDOW_TITLE = "Gesture Studio | Computer Vision Desktop Assistant"
CAMERA_WIDTH = 1280
CAMERA_HEIGHT = 720

PANEL = (22, 29, 40)
TEXT = (239, 244, 250)
MUTED = (158, 173, 190)
MINT = (102, 225, 180)
BLUE = (234, 165, 83)
RED = (92, 102, 245)

GESTURE_GUIDE = (
    ("Index finger only", "Move cursor"),
    ("Thumb + index pinch", "Left click"),
    ("Thumb + middle pinch", "Right click"),
    ("Index + middle pinch", "Double click"),
    ("Thumb + ring pinch", "Drag and drop"),
    ("Index + middle raised", "Play / pause"),
    ("Three / four fingers", "Next / previous"),
    ("Open palm", "Save screenshot"),
    ("Thumbs-up (hold)", "Start / stop recording"),
    ("Thumb + index apart", "Adjust volume"),
)


def draw_label(frame, text: str, position: tuple[int, int], color=TEXT, scale=0.52, thickness=1) -> None:
    """Draw legible anti-aliased text with a subtle dark outline."""

    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, PANEL, thickness + 2, cv2.LINE_AA)
    cv2.putText(frame, text, position, cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw_hud(
    frame,
    gesture_text: str,
    fps: int,
    hand_detected: bool,
    controls_enabled: bool,
    guide_visible: bool,
    frame_reduction: int,
    landmarks: list[Landmark],
    volume_percent: Optional[int] = None,
    feedback_message: str = "",
    recording: bool = False,
) -> None:
    """Render the live dashboard, cursor work area, and optional gesture guide."""

    height, width = frame.shape[:2]
    # Draw the cursor workspace before the translucent panels so its top edge
    # never cuts through the status text.
    margin_x = min(frame_reduction, width // 4)
    margin_y = min(frame_reduction, height // 4)
    region_bottom = height - margin_y
    region_right = width - margin_x
    if guide_visible and width >= 900 and height >= 520:
        region_right = min(region_right, width - 310)
    cv2.line(frame, (margin_x, 116), (margin_x, region_bottom), (110, 146, 137), 1, cv2.LINE_AA)
    cv2.line(frame, (margin_x, region_bottom), (region_right, region_bottom), (110, 146, 137), 1, cv2.LINE_AA)
    if not (guide_visible and width >= 900 and height >= 520):
        cv2.line(frame, (region_right, 116), (region_right, region_bottom), (110, 146, 137), 1, cv2.LINE_AA)

    overlay = frame.copy()

    # A restrained dark glass treatment keeps the camera feed visible under UI.
    cv2.rectangle(overlay, (16, 16), (width - 16, 116), PANEL, cv2.FILLED)
    if guide_visible and width >= 900 and height >= 520:
        cv2.rectangle(overlay, (width - 310, 132), (width - 16, height - 72), PANEL, cv2.FILLED)
    cv2.rectangle(overlay, (16, height - 60), (width - 16, height - 12), PANEL, cv2.FILLED)
    cv2.addWeighted(overlay, 0.84, frame, 0.16, 0, frame)

    # Header and live status.
    draw_label(frame, "GESTURE STUDIO", (34, 52), MINT, 0.82, 2)
    draw_label(frame, "COMPUTER VISION  /  DESKTOP CONTROL", (36, 81), MUTED, 0.39, 1)
    cv2.line(frame, (width // 3, 31), (width // 3, 99), (76, 91, 108), 1, cv2.LINE_AA)

    display_gesture = gesture_text if len(gesture_text) <= 24 else gesture_text[:21] + "..."
    draw_label(frame, "LIVE GESTURE", (width // 3 + 24, 46), MUTED, 0.37, 1)
    draw_label(frame, display_gesture, (width // 3 + 24, 82), MINT if hand_detected else TEXT, 0.68, 2)

    status_x = int(width * 0.70)
    cv2.line(frame, (status_x - 18, 31), (status_x - 18, 99), (76, 91, 108), 1, cv2.LINE_AA)
    status_color = MINT if controls_enabled else BLUE
    status_text = "CONTROLS ACTIVE" if controls_enabled else "CONTROLS PAUSED"
    draw_label(frame, status_text, (status_x, 49), status_color, 0.47, 2)
    hand_text = "HAND TRACKED" if hand_detected else "SHOW ONE HAND"
    draw_label(frame, hand_text, (status_x, 77), MUTED, 0.41, 1)
    if recording:
        cv2.circle(frame, (width - 48, 48), 7, RED, cv2.FILLED, cv2.LINE_AA)
        draw_label(frame, "REC", (width - 88, 54), RED, 0.40, 2)
    detail = f"{fps:02d} FPS"
    if volume_percent is not None:
        detail += f"   |   VOL {volume_percent:02d}%"
    draw_label(frame, detail, (width - 174, 101), MINT, 0.36, 1)

    if landmarks:
        x_min = min(point.x for point in landmarks)
        y_min = min(point.y for point in landmarks)
        x_max = max(point.x for point in landmarks)
        y_max = max(point.y for point in landmarks)
        cv2.rectangle(frame, (x_min - 8, y_min - 8), (x_max + 8, y_max + 8), MINT, 2, cv2.LINE_AA)
        index_tip = landmarks[INDEX_TIP]
        cv2.circle(frame, (index_tip.x, index_tip.y), 8, MINT, cv2.FILLED, cv2.LINE_AA)
        cv2.circle(frame, (index_tip.x, index_tip.y), 13, TEXT, 1, cv2.LINE_AA)

    # Quick reference card for a project demonstration.
    if guide_visible and width >= 900 and height >= 520:
        panel_x = width - 292
        draw_label(frame, "GESTURE QUICK GUIDE", (panel_x, 164), TEXT, 0.49, 2)
        cv2.line(frame, (panel_x, 180), (width - 34, 180), (76, 91, 108), 1, cv2.LINE_AA)
        y = 207
        for gesture, action in GESTURE_GUIDE:
            cv2.circle(frame, (panel_x + 4, y - 5), 3, MINT, cv2.FILLED, cv2.LINE_AA)
            draw_label(frame, gesture, (panel_x + 16, y), MUTED, 0.37, 1)
            draw_label(frame, action, (panel_x + 16, y + 17), TEXT, 0.42, 1)
            y += 41
        draw_label(frame, "SPACE pauses all desktop actions", (panel_x, height - 91), BLUE, 0.35, 1)

    if feedback_message:
        message_width = min(width - 48, max(340, len(feedback_message) * 10))
        left = (width - message_width) // 2
        cv2.rectangle(frame, (left, height - 112), (left + message_width, height - 73), PANEL, cv2.FILLED)
        draw_label(frame, feedback_message, (left + 14, height - 87), MINT, 0.43, 1)

    draw_label(frame, "ESC  QUIT", (34, height - 30), TEXT, 0.39, 1)
    draw_label(frame, "SPACE  PAUSE / RESUME", (176, height - 30), TEXT, 0.39, 1)
    draw_label(frame, "G  TOGGLE GUIDE", (420, height - 30), TEXT, 0.39, 1)
    draw_label(frame, "S  SNAPSHOT", (592, height - 30), TEXT, 0.39, 1)
    draw_label(frame, "R  RECORD", (748, height - 30), TEXT, 0.39, 1)
    draw_label(frame, "PAUSE BEFORE EXPLAINING", (width - 250, height - 30), MUTED, 0.34, 1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Control desktop actions with live hand gestures.")
    parser.add_argument("--camera", type=int, default=0, help="webcam device index (default: 0)")
    parser.add_argument("--width", type=int, default=CAMERA_WIDTH, help="requested camera width")
    parser.add_argument("--height", type=int, default=CAMERA_HEIGHT, help="requested camera height")
    return parser.parse_args()


def main() -> int:
    """Open the selected camera, run gesture actions, and release all devices."""

    args = parse_args()
    backend = cv2.CAP_AVFOUNDATION if platform.system() == "Darwin" else cv2.CAP_ANY
    camera = cv2.VideoCapture(args.camera, backend)
    if not camera.isOpened():
        camera.release()
        print(
            f"Could not open camera {args.camera}. Check camera access in system settings, "
            "close other camera apps, or try --camera 1."
        )
        return 1

    camera.set(cv2.CAP_PROP_FRAME_WIDTH, args.width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, args.height)

    detector: Optional[HandDetector] = None
    mouse: Optional[MouseControl] = None
    screenshots: Optional[ScreenshotManager] = None
    recorder: Optional[SessionRecorder] = None
    controls_enabled = True
    guide_visible = True
    previous_time = time.monotonic()
    smoothed_fps = 0.0
    active_gesture = "WAITING FOR HAND"
    volume_percent: Optional[int] = None
    feedback_message = ""
    feedback_until = 0.0
    record_pose_started_at: Optional[float] = None
    record_pose_triggered = False

    try:
        # Create the GUI context before the MediaPipe graph starts. This is
        # especially important for macOS builds that initialize OpenGL eagerly.
        cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
        try:
            detector = HandDetector()
        except RuntimeError as error:
            if "NSOpenGLPixelFormat" in str(error) or "kGpuService" in str(error):
                raise RuntimeError(
                    "MediaPipe could not create the macOS graphics context. "
                    "Run this app from an active desktop session with camera and display access."
                ) from error
            raise
        gestures = GestureController()
        mouse = MouseControl()
        volume = VolumeControl()
        screenshots = ScreenshotManager()
        recorder = SessionRecorder()
        media = MediaControl()

        while True:
            success, frame = camera.read()
            if not success:
                print("The camera stopped returning frames. Check its connection and permissions.")
                break

            frame = cv2.flip(frame, 1)
            frame = detector.find_hands(frame, draw=True)
            landmarks = detector.get_landmarks(frame)
            frame_height, frame_width = frame.shape[:2]
            volume_percent = None

            if landmarks:
                state = gestures.analyze(landmarks, detector.hand_label)
                active_gesture = state.name
                index_tip = landmarks[INDEX_TIP]

                if controls_enabled:
                    if state.name in {"MOUSE MOVE", "VOLUME CONTROL", "DRAG"}:
                        mouse.move_cursor(index_tip, (frame_width, frame_height))

                    if state.name == "LEFT CLICK" and gestures.can_trigger("left_click"):
                        mouse.left_click()
                    elif state.name == "RIGHT CLICK" and gestures.can_trigger("right_click"):
                        mouse.right_click()
                    elif state.name == "DOUBLE CLICK" and gestures.can_trigger("double_click"):
                        mouse.double_click()
                    elif state.name == "DRAG":
                        mouse.start_drag()
                    else:
                        mouse.stop_drag()

                    if state.name == "VOLUME CONTROL":
                        volume_percent, _ = volume.set_volume_by_distance(state.distances["thumb_index"])

                    if state.name == "SCREENSHOT" and gestures.can_trigger("screenshot"):
                        try:
                            saved_path: Path = screenshots.capture()
                            feedback_message = f"Screenshot saved  |  {saved_path.name}"
                            feedback_until = time.monotonic() + 2.5
                            print(f"Screenshot saved: {saved_path}")
                        except Exception as error:
                            feedback_message = "Screenshot could not be saved"
                            feedback_until = time.monotonic() + 2.5
                            print(f"Screenshot failed: {error}")

                    # Hold a thumbs-up briefly to toggle recording once. The
                    # pose must be lowered before it can toggle recording again.
                    if state.name == "RECORD" and controls_enabled:
                        if record_pose_started_at is None:
                            record_pose_started_at = time.monotonic()
                        elif not record_pose_triggered and time.monotonic() - record_pose_started_at >= 0.7:
                            record_pose_triggered = True
                            try:
                                if recorder.is_recording:
                                    saved_path = recorder.stop()
                                    feedback_message = f"Recording saved  |  {saved_path.name if saved_path else ''}"
                                    if saved_path:
                                        print(f"Demo video saved: {saved_path}")
                                else:
                                    saved_path = recorder.start(frame)
                                    feedback_message = "Recording started  |  Thumbs-up to stop"
                                    print(f"Recording demo video: {saved_path}")
                            except Exception as error:
                                feedback_message = "Video recording could not start"
                                print(f"Video recording failed: {error}")
                            feedback_until = time.monotonic() + 2.5
                    else:
                        record_pose_started_at = None
                        record_pose_triggered = False

                    if state.name == "PLAY/PAUSE" and gestures.can_trigger("play_pause"):
                        media.play_pause()
                    elif state.name == "NEXT TRACK" and gestures.can_trigger("next_track"):
                        media.next_track()
                    elif state.name == "PREVIOUS TRACK" and gestures.can_trigger("previous_track"):
                        media.previous_track()
                else:
                    mouse.stop_drag()
                    record_pose_started_at = None
                    record_pose_triggered = False
            else:
                active_gesture = "WAITING FOR HAND"
                record_pose_started_at = None
                record_pose_triggered = False
                mouse.stop_drag()

            current_time = time.monotonic()
            delta = current_time - previous_time
            previous_time = current_time
            if delta > 0:
                instantaneous_fps = 1.0 / delta
                smoothed_fps = instantaneous_fps if smoothed_fps == 0 else 0.82 * smoothed_fps + 0.18 * instantaneous_fps

            if current_time >= feedback_until:
                feedback_message = ""

            draw_hud(
                frame,
                active_gesture,
                int(smoothed_fps),
                bool(landmarks),
                controls_enabled,
                guide_visible,
                mouse.frame_reduction,
                landmarks,
                volume_percent,
                feedback_message,
                recorder.is_recording,
            )
            recorder.write(frame)
            cv2.imshow(WINDOW_TITLE, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q")):
                break
            if key == ord(" "):
                controls_enabled = not controls_enabled
                if not controls_enabled:
                    mouse.stop_drag()
                feedback_message = "Desktop actions resumed" if controls_enabled else "Desktop actions paused"
                feedback_until = time.monotonic() + 1.8
            elif key in (ord("g"), ord("G")):
                guide_visible = not guide_visible
            elif key in (ord("s"), ord("S")):
                try:
                    saved_path = screenshots.capture_frame(frame)
                    feedback_message = f"Preview saved  |  {saved_path.name}"
                    print(f"Preview image saved: {saved_path}")
                except Exception as error:
                    feedback_message = "Preview image could not be saved"
                    print(f"Preview image failed: {error}")
                feedback_until = time.monotonic() + 2.5
            elif key in (ord("r"), ord("R")):
                try:
                    if recorder.is_recording:
                        saved_path = recorder.stop()
                        feedback_message = f"Recording saved  |  {saved_path.name if saved_path else ''}"
                        if saved_path:
                            print(f"Demo video saved: {saved_path}")
                    else:
                        saved_path = recorder.start(frame)
                        feedback_message = "Recording started  |  Press R to stop"
                        print(f"Recording demo video: {saved_path}")
                except Exception as error:
                    feedback_message = "Video recording could not start"
                    print(f"Video recording failed: {error}")
                feedback_until = time.monotonic() + 2.5

    except KeyboardInterrupt:
        print("Application interrupted by user.")
    except Exception as error:
        print(f"Application stopped: {error}")
        return 1
    finally:
        if recorder is not None:
            saved_path = recorder.stop()
            if saved_path:
                print(f"Demo video saved: {saved_path}")
        if mouse is not None:
            try:
                mouse.stop_drag()
            except Exception:
                pass
        camera.release()
        cv2.destroyAllWindows()
        if detector is not None:
            detector.close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
