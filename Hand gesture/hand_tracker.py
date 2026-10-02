"""
Hand Tracker and Gesture Recognition Engine using OpenCV and MediaPipe Tasks.
Robust camera opening across backends and reliable gesture recognition.
"""

import os
import cv2
import numpy as np
import pygame
import mediapipe as mp

from config import CAM_WIDTH, CAM_HEIGHT, STEER_DEADZONE, JUMP_COOLDOWN_MS

HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index
    (5, 9), (9, 10), (10, 11), (11, 12),   # Middle
    (9, 13), (13, 14), (14, 15), (15, 16), # Ring
    (13, 17), (17, 18), (18, 19), (19, 20),# Pinky
    (0, 17)                                # Palm base
]


class HandTracker:
    def __init__(self, camera_index=0, model_path=None):
        self.camera_available = False
        self.cap = None
        self.landmarker = None
        self.last_jump_time = 0
        self.prev_hand_y = None
        self.pip_surface = None
        self.camera_index = camera_index
        self.status_message = "Initializing..."

        # Gesture states
        self.steer_value = 0.0   # [-1.0 (full left), 1.0 (full right)]
        self.is_jumping = False
        self.is_braking = False
        self.hand_detected = False
        self.gesture_name = "SEARCHING FOR HAND"

        # Resolve absolute path to model file
        base_dir = os.path.dirname(os.path.abspath(__file__))
        if model_path is None:
            model_path = os.path.join(base_dir, "hand_landmarker.task")
        elif not os.path.isabs(model_path):
            model_path = os.path.join(base_dir, model_path)

        # Check model file exists
        if not os.path.exists(model_path):
            print(f"[HandTracker] Error: Model file not found at {model_path}")
            self.status_message = "Model file not found"
            return

        try:
            BaseOptions = mp.tasks.BaseOptions
            HandLandmarker = mp.tasks.vision.HandLandmarker
            HandLandmarkerOptions = mp.tasks.vision.HandLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = HandLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=VisionRunningMode.IMAGE,
                min_hand_detection_confidence=0.35,
                min_hand_presence_confidence=0.35,
                min_tracking_confidence=0.35,
                num_hands=1
            )
            self.landmarker = HandLandmarker.create_from_options(options)
            print("[HandTracker] MediaPipe HandLandmarker loaded successfully.")
        except Exception as e:
            print(f"[HandTracker] Error initializing MediaPipe: {e}")
            self.status_message = f"MediaPipe error: {e}"
            return

        # Attempt to open webcam across backends and indices
        self._init_camera()

    def _init_camera(self):
        """Attempts to open camera using DirectShow and default backends across indices 0..2."""
        backends = []
        if hasattr(cv2, 'CAP_DSHOW'):
            backends.append((cv2.CAP_DSHOW, "DirectShow"))
        backends.append((cv2.CAP_ANY, "Default"))

        indices = [self.camera_index] + [i for i in [0, 1, 2] if i != self.camera_index]

        for idx in indices:
            for backend, b_name in backends:
                try:
                    cap = cv2.VideoCapture(idx, backend)
                    if cap.isOpened():
                        ret, test_frame = cap.read()
                        if ret and test_frame is not None:
                            cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAM_WIDTH)
                            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAM_HEIGHT)
                            self.cap = cap
                            self.camera_available = True
                            self.camera_index = idx
                            self.status_message = f"Connected (Cam {idx}, {b_name})"
                            print(f"[HandTracker] Camera connected successfully on index {idx} ({b_name}).")
                            return
                        cap.release()
                except Exception as e:
                    print(f"[HandTracker] Debug cam {idx} ({b_name}) failed: {e}")
                    continue

        self.camera_available = False
        self.status_message = "No webcam detected"
        print("[HandTracker] Notice: No webcam could be opened. Keyboard controls (A/D/Space) active.")

    def update(self):
        """Captures frame, runs hand detection, updates gestures, and creates PiP surface."""
        self.is_jumping = False
        current_time = pygame.time.get_ticks()

        if not self.camera_available or self.cap is None:
            self.hand_detected = False
            self.gesture_name = "KEYBOARD MODE"
            self.steer_value = 0.0
            return

        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.hand_detected = False
            return

        # Resize to fixed standard CAM_WIDTH, CAM_HEIGHT for consistent tracking & fast speed
        if frame.shape[1] != CAM_WIDTH or frame.shape[0] != CAM_HEIGHT:
            frame = cv2.resize(frame, (CAM_WIDTH, CAM_HEIGHT))

        # Flip horizontally for intuitive selfie mirror view
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        # Convert to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        try:
            result = self.landmarker.detect(mp_image)
        except Exception:
            result = None

        if result and result.hand_landmarks and len(result.hand_landmarks) > 0:
            self.hand_detected = True
            landmarks = result.hand_landmarks[0]

            # Analyze gesture
            self._analyze_gesture(landmarks, current_time)

            # Draw landmarks and connections with color coding
            self._draw_landmarks(frame, landmarks, w, h)
        else:
            self.hand_detected = False
            # Smoothly decay steering when hand is lost
            self.steer_value *= 0.6
            if abs(self.steer_value) < 0.05:
                self.steer_value = 0.0
            self.is_braking = False
            self.gesture_name = "SHOW HAND TO PLAY"
            self.prev_hand_y = None

        # Draw HUD overlays on camera frame
        self._draw_frame_hud(frame, w, h)

        # Convert OpenCV frame to Pygame Surface for PiP display
        rgb_display = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        transposed = np.transpose(rgb_display, (1, 0, 2))
        self.pip_surface = pygame.surfarray.make_surface(transposed)

    def _analyze_gesture(self, lms, current_time):
        """Analyzes 21 3D landmarks for steering, jumping, and braking."""
        # Palm center calculated from wrist (0) and knuckle bases (5, 9, 13, 17)
        palm_x = (lms[0].x + lms[5].x + lms[9].x + lms[13].x + lms[17].x) / 5.0
        palm_y = (lms[0].y + lms[5].y + lms[9].y + lms[13].y + lms[17].y) / 5.0

        # 1. Steering: normalized x relative to 0.5 center
        dx = palm_x - 0.5
        deadzone = 0.08
        if abs(dx) > deadzone:
            magnitude = (abs(dx) - deadzone) / 0.25
            target_steer = np.clip(np.sign(dx) * magnitude, -1.0, 1.0)
            # Smooth steering to prevent jitter
            self.steer_value = self.steer_value * 0.5 + target_steer * 0.5
        else:
            self.steer_value *= 0.5
            if abs(self.steer_value) < 0.05:
                self.steer_value = 0.0

        # 2. Fist / Brake Detection
        wrist = np.array([lms[0].x, lms[0].y])
        fist_count = 0
        for tip_idx, mcp_idx in [(8, 5), (12, 9), (16, 13), (20, 17)]:
            tip = np.array([lms[tip_idx].x, lms[tip_idx].y])
            mcp = np.array([lms[mcp_idx].x, lms[mcp_idx].y])
            if np.linalg.norm(tip - wrist) < np.linalg.norm(mcp - wrist) * 1.15:
                fist_count += 1

        is_fist = (fist_count >= 3)
        self.is_braking = is_fist

        # 3. Jump Detection:
        # A) Index finger extended upward (tip above PIP joint and MCP joint)
        index_pointing_up = (lms[8].y < lms[6].y) and (lms[8].y < lms[5].y)
        # B) Hand positioned high in the camera frame
        hand_raised_high = (palm_y < 0.38)
        # C) Rapid upward movement
        rapid_upward = False
        if self.prev_hand_y is not None:
            dy = palm_y - self.prev_hand_y
            if dy < -0.045:
                rapid_upward = True

        self.prev_hand_y = palm_y

        # Trigger jump
        if not is_fist and (index_pointing_up or hand_raised_high or rapid_upward):
            if current_time - self.last_jump_time > JUMP_COOLDOWN_MS:
                self.is_jumping = True
                self.last_jump_time = current_time

        # Update gesture status name for UI
        if self.is_braking:
            self.gesture_name = "BRAKE / STOP"
            self.steer_value = 0.0
        elif self.is_jumping:
            self.gesture_name = "JUMP!"
        elif self.steer_value > 0.15:
            self.gesture_name = f"ROLL RIGHT ({int(self.steer_value * 100)}%)"
        elif self.steer_value < -0.15:
            self.gesture_name = f"ROLL LEFT ({int(abs(self.steer_value) * 100)}%)"
        else:
            self.gesture_name = "STEADY / NEUTRAL"

    def _draw_landmarks(self, frame, landmarks, w, h):
        """Draws glowing skeleton on camera frame with gesture-aware colors."""
        points = []
        for lm in landmarks:
            cx = max(0, min(w - 1, int(lm.x * w)))
            cy = max(0, min(h - 1, int(lm.y * h)))
            points.append((cx, cy))

        # Dynamic bone color based on action
        if self.is_jumping:
            bone_color = (80, 255, 120)   # Vivid Green
        elif self.is_braking:
            bone_color = (60, 60, 255)    # Red
        elif abs(self.steer_value) > 0.15:
            bone_color = (0, 220, 255)    # Cyan / Yellow
        else:
            bone_color = (0, 200, 240)

        # Draw bones
        for start_idx, end_idx in HAND_CONNECTIONS:
            p1, p2 = points[start_idx], points[end_idx]
            cv2.line(frame, p1, p2, bone_color, 2, cv2.LINE_AA)

        # Draw joints
        for idx, pt in enumerate(points):
            if idx in [4, 8, 12, 16, 20]:
                cv2.circle(frame, pt, 6, (0, 255, 160), -1, cv2.LINE_AA)
                cv2.circle(frame, pt, 7, (255, 255, 255), 1, cv2.LINE_AA)
            else:
                cv2.circle(frame, pt, 4, (255, 120, 50), -1, cv2.LINE_AA)

    def _draw_frame_hud(self, frame, w, h):
        """Renders overlay guides, center line, and active gesture badge."""
        # Deadzone guide lines
        deadzone = 0.08
        x1 = int((0.5 - deadzone) * w)
        x2 = int((0.5 + deadzone) * w)
        cv2.line(frame, (x1, 0), (x1, h - 28), (80, 80, 80), 1, cv2.LINE_AA)
        cv2.line(frame, (x2, 0), (x2, h - 28), (80, 80, 80), 1, cv2.LINE_AA)
        cv2.line(frame, (w // 2, 0), (w // 2, h - 28), (110, 110, 110), 1, cv2.LINE_AA)

        # Bottom banner
        banner_color = (30, 35, 45)
        text_color = (255, 255, 255)
        if self.is_jumping:
            banner_color = (0, 160, 60)
        elif self.is_braking:
            banner_color = (40, 40, 200)
        elif abs(self.steer_value) > 0.15:
            banner_color = (200, 110, 20)

        cv2.rectangle(frame, (0, h - 28), (w, h), banner_color, -1)
        cv2.putText(
            frame, self.gesture_name, (10, h - 8),
            cv2.FONT_HERSHEY_SIMPLEX, 0.48, text_color, 1, cv2.LINE_AA
        )

    def close(self):
        """Releases camera and model resources."""
        if self.cap:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None
        if self.landmarker:
            try:
                self.landmarker.close()
            except Exception:
                pass
            self.landmarker = None
