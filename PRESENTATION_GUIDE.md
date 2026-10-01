# Project presentation guide

## 30-second opening

“Gesture Studio is a touch-free desktop assistant built with computer vision. A webcam observes one hand, MediaPipe returns 21 hand landmarks, and a small gesture layer maps hand poses to cursor, click, volume, media, and screenshot actions. The goal is to make common desktop interactions accessible without a mouse, while keeping the system lightweight enough to run live.”

## Suggested 5-minute presentation

1. **Problem and goal — 30 seconds**  
   Explain that a standard mouse is not always convenient. This prototype explores hands-free desktop interaction using a camera already available on many computers.

2. **System design — 60 seconds**  
   Walk through the flow in the README: webcam frame → OpenCV → MediaPipe landmarks → gesture rules → operating-system action. Emphasize that MediaPipe supplies pretrained hand tracking; the project focuses on the gesture interface and desktop integration.

3. **Show the live dashboard — 30 seconds**  
   Point out the current gesture, hand-tracking status, live frame rate, cursor-mapping boundary, quick guide, and the Space pause control.

4. **Live demonstration — 2 minutes**  
   Move the cursor with the index finger. Demonstrate a left click, a two-finger play/pause gesture, and volume adjustment. Use an open palm for a full-desktop screenshot. Hold a thumbs-up briefly to start recording the annotated camera preview, then lower the thumb and repeat the thumbs-up to stop and save the MP4. Show the saved files. Pause actions with Space before returning to the slides.

5. **Engineering choices and limits — 60 seconds**  
   Explain that pinch distances scale with hand size, cursor movement is smoothed, repeated actions use cooldowns, and the pause key prevents accidental actions during setup. Mention that lighting, camera quality, hand orientation, and heuristic gesture rules still affect recognition.

## Live demo checklist

- Install dependencies and launch the app before presenting.
- Grant camera and Accessibility permissions in advance, then restart the app.
- Close video-call or camera apps that may reserve the webcam.
- Use even front lighting and a clear background.
- Keep the desktop clear; cursor and clicks affect the real computer.
- Start with the gesture guide visible. Keep the **Space** key ready to pause actions.
- Click the Gesture Studio preview window before using **S**, **R**, **Space**, or **G**.
- Use a local audio track if demonstrating media controls.
- **S** saves only the annotated camera preview in `screenshots/`; the open-palm gesture captures the desktop in the same folder.
- A held thumbs-up starts/stops recording the annotated camera preview. It saves an MP4 in `recordings/`, with no desktop content or audio. Lower the thumb between toggles, and keep only the intended presenter/hand in view. **R** remains an alternate keyboard shortcut.
- Pause actions with **Space** before explaining or switching apps.
- If tracking is unreliable, skip to the architecture explanation instead of spending presentation time troubleshooting.

## What to say about evaluation

The app reports live frames per second, but FPS is not a measure of gesture accuracy. Do not claim an accuracy percentage unless you have measured it. For a measured evaluation, record a fixed set of gesture attempts under consistent lighting and camera distance, then report:

| Measure | How to collect it |
| --- | --- |
| Gesture success rate | Correctly recognized attempts ÷ total attempts for each gesture |
| Response time | Time from forming a gesture to the visible action |
| Stability | False triggers while holding a neutral pose |
| Runtime performance | FPS displayed by the app during the same trial |

Include the number of attempts, camera, environment, and lighting so the results are reproducible.

## Likely viva questions

**Why use MediaPipe?**  
It provides hand landmarks directly, so the prototype can focus on interaction logic instead of training a hand detector from scratch.

**What does OpenCV do?**  
It captures and transforms webcam frames, displays the live interface, and draws landmarks and status information.

**How does the app recognize a pinch?**  
It measures the pixel distance between selected fingertip landmarks. The threshold scales with the detected palm width so the gesture remains usable when the hand moves nearer or farther from the camera.

**How are accidental repeated actions reduced?**  
Discrete actions such as clicks and screenshots have a cooldown. Desktop actions can also be paused with Space.

**What does the recording feature save?**  
It saves the annotated webcam preview as a local MP4 for a demo replay. It does not record the desktop or audio.

**Is this a trained custom AI model?**  
No. Hand tracking uses MediaPipe’s pretrained model. The gesture mapping is implemented as geometric rules over landmarks.

**What are the main limitations?**  
Low light, occlusion, camera angle, and differences in hand pose can affect landmark quality. Gesture rules are a prototype and may need personalization for different users.

**What would you improve next?**  
Collect consented gesture samples, measure per-gesture accuracy and latency, add calibration for each user, and compare the current rules with a trained temporal gesture classifier.
