import cv2
import time
import numpy as np
import sounddevice as sd
from hand_tracker import HandTracker
from simulation import Particle, Ripple, MatrixEffect, Theme

# Audio Constants
SAMPLE_RATE = 44100
audio_time = 0

def generate_tone(freq, duration, volume=0.1):
    t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
    wave = volume * np.sin(2 * np.pi * freq * t)
    sd.play(wave, SAMPLE_RATE)

def main():
    # Setup Camera
    w_cam, h_cam = 1280, 720
    cap = cv2.VideoCapture(0)
    cap.set(3, w_cam)
    cap.set(4, h_cam)

    detector = HandTracker(detection_con=0.7, track_con=0.7)
    matrix = MatrixEffect(w_cam, h_cam)
    
    particles = []
    ripples = []
    
    current_theme = Theme.RAINBOW
    themes_list = [Theme.RAINBOW, Theme.CYBERPUNK, Theme.LAVA, Theme.OCEAN, Theme.GALAXY]
    theme_idx = 0

    p_time = 0
    start_time = time.time()
    last_pinch_states = [False, False]
    hand_vel = 0

    print("Advanced Hand Tracking AR Started")
    print("Press 't' to change Theme")
    print("Pinch (Index + Thumb) to trigger Shockwave")
    print("Press 'q' to exit")

    while True:
        success, img = cap.read()
        if not success: break
        
        img = cv2.flip(img, 1)
        curr_time = time.time() - start_time
        
        # Detect Hands
        img, hands = detector.find_hands(img, draw=False)
        
        # Calculate Hand Velocity for Matrix Effect
        if len(hands) > 0:
            # Simple avg distance of index tip movement
            # In a real app we'd track last pos, here we'll approximate based on hand count
            hand_vel = len(hands) * 0.5
        else:
            hand_vel = 0

        # Create Transparent Overlay for effects
        overlay = np.zeros_like(img)
        
        # 1. Background Matrix Effect
        theme_col = Theme.get_color(current_theme, curr_time, 0, 1)
        matrix.draw(overlay, theme_col, hand_vel)

        # 2. Process Gestures and Effects
        for idx, hand in enumerate(hands):
            glow_col = Theme.get_color(current_theme, curr_time, idx, 2)
            
            # Draw Hand Skeleton with Glow
            for connection in HandTracker.HAND_CONNECTIONS:
                p1 = hand[connection[0]]
                p2 = hand[connection[1]]
                cv2.line(overlay, (p1['x'], p1['y']), (p2['x'], p2['y']), glow_col, 2)

            # Pinch Detection
            thumb_tip = hand[4]
            index_tip = hand[8]
            dist = detector.get_distance(thumb_tip, index_tip)
            
            is_pinching = dist < 40
            if is_pinching and not last_pinch_states[idx if idx < 2 else 0]:
                # Trigger Ripple/Shockwave
                mid_x = (thumb_tip['x'] + index_tip['x']) // 2
                mid_y = (thumb_tip['y'] + index_tip['y']) // 2
                ripples.append(Ripple(mid_x, mid_y, glow_col))
                # Trigger "Zap" sound
                try: generate_tone(800 + idx*200, 0.1, volume=0.05)
                except: pass
                
            if idx < 2: last_pinch_states[idx] = is_pinching

            # Finger Tip Particles
            for tip_id in [4, 8, 12, 16, 20]:
                pt = hand[tip_id]
                cv2.circle(overlay, (pt['x'], pt['y']), 5, (255, 255, 255), -1)
                if np.random.random() > 0.7:
                    particles.append(Particle(pt['x'], pt['y'], glow_col))

        # 3. Connection between hands (Lightning effect)
        if len(hands) >= 2:
            h1, h2 = hands[0], hands[1]
            for tip_id in [4, 8, 12, 16, 20]:
                p1, p2 = h1[tip_id], h2[tip_id]
                d = detector.get_distance(p1, p2)
                if d < 300:
                    mid_col = Theme.get_color(current_theme, curr_time, tip_id, 20)
                    cv2.line(overlay, (p1['x'], p1['y']), (p2['x'], p2['y']), mid_col, 1)
                    # Add jitter for lightning look
                    if np.random.random() > 0.5:
                        mx, my = (p1['x']+p2['x'])//2, (p1['y']+p2['y'])//2
                        mx += np.random.randint(-20, 20)
                        my += np.random.randint(-20, 20)
                        cv2.line(overlay, (p1['x'], p1['y']), (mx, my), (255, 255, 255), 1)
                        cv2.line(overlay, (mx, my), (p2['x'], p2['y']), (255, 255, 255), 1)

        # Update and Draw Particles/Ripples
        particles = [p for p in particles if p.update()]
        for p in particles: p.draw(overlay)
        
        ripples = [r for r in ripples if r.update()]
        for r in ripples: r.draw(overlay)

        # Merge Overlay with Camera Image
        # Make camera image darker for AR feel
        img = cv2.addWeighted(img, 0.3, np.zeros_like(img), 0.7, 0)
        img = cv2.addWeighted(img, 1.0, overlay, 1.0, 0)

        # 4. HUD
        fps = 1 / (time.time() - p_time) if (time.time() - p_time) > 0 else 0
        p_time = time.time()
        
        cv2.rectangle(img, (20, 20), (300, 150), (30, 30, 30), -1)
        cv2.rectangle(img, (20, 20), (300, 150), (200, 200, 200), 1)
        cv2.putText(img, f"FPS: {int(fps)}", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(img, f"Hands: {len(hands)}", (40, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.putText(img, f"Theme: {current_theme}", (40, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, theme_col, 2)
        
        cv2.putText(img, "Press 'T' for Theme", (w_cam-250, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Advanced Hand Tracking AR", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('t'):
            theme_idx = (theme_idx + 1) % len(themes_list)
            current_theme = themes_list[theme_idx]

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
