# 🌌 Hand-Tracking Anti-Gravity Controller (Python Edition)

Experience the "Force" directly through your webcam. This project uses real-time hand-landmarks to create a physics-based simulation where you can manipulate digital particles with your hands.

## 🚀 Features
- **Real-time 21-point hand tracking** via MediaPipe.
- **Gesture-based Physics**:
  - **Open Palm (Push)**: Repels particles away from your hand.
  - **Closed Fist (Pull)**: Attracts particles towards your hand.
- **Anti-Gravity Simulation**: Particles with momentum, friction, and glowing aesthetics.
- **Low-Latency execution** optimized for Python.

## 🛠 Prerequisites
- Python 3.8+
- Webcam

## 📦 Installation
```bash
pip install -r requirements.txt
```

## 🎮 How to Use
1. Run the script:
   ```bash
   python main.py
   ```
2. Wait for the camera to initialize.
3. **Pushing (Force)**: Keep your hand open to push particles.
4. **Pulling (Gravity)**: Close your hand into a fist to draw particles in.
5. Press `q` to exit.

## 💻 Technical Stack
- **OpenCV**: Visualization and image processing.
- **MediaPipe**: Hand landmark detection.
- **NumPy**: Vector-based physics calculations.
