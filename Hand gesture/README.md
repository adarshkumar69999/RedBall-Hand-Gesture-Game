# Red Ball: Hand Gesture Adventure 🔴🖐️

An interactive, physics-driven platformer adventure inspired by the classic **Red Ball** game, controlled entirely using real-time computer vision hand gestures via your webcam!

---

## 🎮 How to Play & Controls

The game tracks your hand in real time using Google MediaPipe and OpenCV. A Picture-in-Picture (PiP) feed in the top right shows your hand tracking skeleton and active gesture badges.

### Hand Gestures
| Gesture | Action | Description |
| :--- | :--- | :--- |
| **Move Hand Left / Right** | **Roll Left / Right** | Position your hand left or right of the center line to steer. Further out = faster acceleration! |
| **Point Index Finger Up / Quick Upward Swipe** | **Jump / Super Leap** | Point your index finger upward or quickly flick your hand up to jump over spikes and across pits. |
| **Close Fist** | **Brake / Stop** | Clench your hand into a fist to instantly brake and stop the ball on narrow platforms. |
| **Open Palm / Center** | **Neutral / Coast** | Keep your hand relaxed near the center to let natural physics and momentum roll the ball. |

### Keyboard Fallback / Alternate Controls
You can play using keyboard controls anytime (simultaneously supported):
- **`A` / `D`** or **Left / Right Arrow**: Roll Left / Right
- **`Spacebar` / `W` / Up Arrow**: Jump
- **`S` / Down Arrow**: Brake
- **`C`**: Toggle Camera Picture-in-Picture (PiP) window on/off
- **`ESC`**: Pause / Resume
- **`R`**: Restart current level / Play again

---

## 🌟 Key Features

- **Physically Responsive Red Ball**: 
  - Dynamic rolling physics with acceleration, friction, momentum, air resistance, and rotational traction.
  - **Animated Expressions**: Realistic squash and stretch deformation upon landing or launching, animated blinking eyes that look toward the direction of velocity, and reactive facial expressions.
- **3 Unique Levels**:
  - **Level 1 (Rolling Meadows)**: Gentle rolling slopes, platform gaps, collectible stars, bounce springs.
  - **Level 2 (The Spiked Valley)**: Moving platforms, dangerous spike clusters, high spring jumps.
  - **Level 3 (Cloud Peaks)**: High-altitude parkour, moving vertical/horizontal platforms, spike fortress, and the golden trophy goal.
- **No External Assets Required**:
  - Self-contained procedural audio synthesizer generates retro 8-bit sound effects (jumps, springs, star chimes, buzz damage, victory fanfares) directly in Python.
- **Visual Polish**:
  - Parallax scrolling background with distant mountains and floating clouds.
  - Dynamic particle systems for dust clouds, golden starbursts, and spring shockwaves.
- **Built for Modern Python**:
  - Fully compatible with Python 3.14 via `pygame-ce` (Community Edition).

---

## 🚀 Quick Start

### 1. Requirements
Ensure dependencies are installed:
```bash
pip install -r requirements.txt
```

### 2. Run the Game
```bash
python main.py
```

### 3. Run Automated Tests
```bash
python test_game.py
```
