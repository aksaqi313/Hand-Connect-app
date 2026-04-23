import cv2
import mediapipe as mp
import numpy as np
import time
import random
import sounddevice as sd

# ==========================================
# 1. AUDIO UTILITIES
# ==========================================
SAMPLE_RATE = 44100

def generate_tone(freq, duration, volume=0.05):
    """Generates a simple sine wave tone."""
    try:
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration))
        wave = volume * np.sin(2 * np.pi * freq * t)
        sd.play(wave, SAMPLE_RATE)
    except:
        pass # Handle cases where audio device is busy

# ==========================================
# 2. HAND TRACKING ENGINE
# ==========================================
class HandTracker:
    def __init__(self, mode=False, max_hands=2, detection_con=0.7, track_con=0.7):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=mode,
            max_num_hands=max_hands,
            min_detection_confidence=detection_con,
            min_tracking_confidence=track_con
        )
        self.mp_draw = mp.solutions.drawing_utils
        self.tip_ids = [4, 8, 12, 16, 20]

    def find_hands(self, img, draw=False):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(img_rgb)
        
        hands_data = []
        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    self.mp_draw.draw_landmarks(img, hand_lms, self.mp_hands.HAND_CONNECTIONS)
                
                lm_list = []
                h, w, c = img.shape
                for id, lm in enumerate(hand_lms.landmark):
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    lm_list.append({'id': id, 'x': cx, 'y': cy})
                hands_data.append(lm_list)
        return img, hands_data

    @staticmethod
    def get_distance(p1, p2):
        return np.hypot(p1['x'] - p2['x'], p1['y'] - p2['y'])

# ==========================================
# 3. VISUAL EFFECTS ENGINE
# ==========================================
class Theme:
    RAINBOW, CYBERPUNK, LAVA, OCEAN, GALAXY = "Rainbow", "Cyberpunk", "Lava", "Ocean", "Galaxy"

    @staticmethod
    def get_color(theme_name, t, index, total):
        total = max(1, total)
        if theme_name == Theme.RAINBOW:
            hue = int((t * 100 + index * (180 / total)) % 180)
            img_hsv = np.uint8([[[hue, 255, 255]]])
            return tuple(map(int, cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)[0][0]))
        elif theme_name == Theme.CYBERPUNK:
            return (60, 0, 255) if index % 2 == 0 else (255, 240, 0)
        elif theme_name == Theme.LAVA:
            hue = int((10 + (index * 5)) % 20)
            val = int(127 + np.sin(t) * 50)
            return tuple(map(int, cv2.cvtColor(np.uint8([[[hue, 255, val]]]), cv2.COLOR_HSV2BGR)[0][0]))
        elif theme_name == Theme.OCEAN:
            hue = int((90 + (index * 10)) % 120)
            return tuple(map(int, cv2.cvtColor(np.uint8([[[hue, 255, 200]]]), cv2.COLOR_HSV2BGR)[0][0]))
        else: # GALAXY
            hue = int((130 + np.sin(t * 2 + index) * 20) % 180)
            return tuple(map(int, cv2.cvtColor(np.uint8([[[hue, 150, 200]]]), cv2.COLOR_HSV2BGR)[0][0]))

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = (random.random() - 0.5) * 12, (random.random() - 0.5) * 12
        self.life, self.color, self.size = 1.0, color, random.randint(2, 5)
    def update(self):
        self.x += self.vx; self.y += self.vy; self.vy += 0.2; self.life -= 0.03
        return self.life > 0
    def draw(self, img):
        c = tuple(map(lambda x: int(x * self.life), self.color))
        cv2.circle(img, (int(self.x), int(self.y)), self.size, c, -1)

class Ripple:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.radius, self.max_radius, self.life, self.color = 0, random.randint(120, 220), 1.0, color
    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.2; self.life -= 0.05
        return self.life > 0
    def draw(self, img):
        thick = max(1, int(4 * self.life))
        cv2.circle(img, (int(self.x), int(self.y)), int(self.radius), self.color, thick)

class MatrixEffect:
    def __init__(self, w, h):
        self.w, self.h, self.font_size = w, h, 18
        self.cols = w // self.font_size
        self.drops = [random.random() * h/self.font_size for _ in range(self.cols)]
    def draw(self, img, color, hand_vel):
        speed = 1.0 + (hand_vel * 2.0)
        for i in range(len(self.drops)):
            if random.random() > 0.95:
                char = chr(random.randint(0x30A0, 0x30FF))
                y = int(self.drops[i] * self.font_size)
                if y < self.h: cv2.putText(img, char, (i * self.font_size, y), cv2.FONT_HERSHEY_PLAIN, 1.2, color, 1)
            self.drops[i] += random.random() * speed
            if self.drops[i] * self.font_size > self.h and random.random() > 0.9: self.drops[i] = 0

# ==========================================
# 4. MAIN APPLICATION LOOP
# ==========================================
def main():
    w_cam, h_cam = 1280, 720
    cap = cv2.VideoCapture(0)
    cap.set(3, w_cam); cap.set(4, h_cam)

    detector = HandTracker()
    matrix = MatrixEffect(w_cam, h_cam)
    particles, ripples = [], []
    
    themes = [Theme.RAINBOW, Theme.CYBERPUNK, Theme.LAVA, Theme.OCEAN, Theme.GALAXY]
    theme_idx, start_time, p_time = 0, time.time(), 0
    last_pinches = [False, False]

    print("ALL-IN-ONE Tracker Started!\n'T' to cycle themes\n'Q' to exit")

    while True:
        success, img = cap.read()
        if not success: break
        
        img = cv2.flip(img, 1)
        curr_t = time.time() - start_time
        img, hands = detector.find_hands(img)
        overlay = np.zeros_like(img)
        
        # Background Matrix
        theme_name = themes[theme_idx]
        t_col = Theme.get_color(theme_name, curr_t, 0, 1)
        matrix.draw(overlay, t_col, len(hands))

        for idx, hand in enumerate(hands):
            glow = Theme.get_color(theme_name, curr_t, idx, 2)
            
            # Skeleton
            for conn in detector.mp_hands.HAND_CONNECTIONS:
                p1, p2 = hand[conn[0]], hand[conn[1]]
                cv2.line(overlay, (p1['x'], p1['y']), (p2['x'], p2['y']), glow, 2)

            # Pinch & Sparkle
            thumb, index = hand[4], hand[8]
            is_pinching = detector.get_distance(thumb, index) < 40
            if is_pinching and not last_pinches[idx if idx < 2 else 0]:
                ripples.append(Ripple((thumb['x']+index['x'])//2, (thumb['y']+index['y'])//2, glow))
                generate_tone(800 + idx*200, 0.1)
            if idx < 2: last_pinches[idx] = is_pinching

            for tip in [4, 8, 12, 16, 20]:
                pt = hand[tip]
                if random.random() > 0.7: particles.append(Particle(pt['x'], pt['y'], glow))

        # Hand-to-Hand Lightning
        if len(hands) >= 2:
            h1, h2 = hands[0], hands[1]
            for tip in [4, 8, 12, 16, 20]:
                p1, p2 = h1[tip], h2[tip]
                if detector.get_distance(p1, p2) < 300:
                    cv2.line(overlay, (p1['x'], p1['y']), (p2['x'], p2['y']), Theme.get_color(theme_name, curr_t, tip, 5), 1)

        # Rendering
        particles = [p for p in particles if p.update()]
        for p in particles: p.draw(overlay)
        ripples = [r for r in ripples if r.update()]
        for r in ripples: r.draw(overlay)

        img = cv2.addWeighted(cv2.addWeighted(img, 0.3, np.zeros_like(img), 0.7, 0), 1.0, overlay, 1.0, 0)
        
        # HUD
        cv2.rectangle(img, (20, 20), (300, 150), (30, 30, 30), -1)
        fps = int(1 / (time.time() - p_time)) if (time.time() - p_time) > 0 else 0
        p_time = time.time()
        cv2.putText(img, f"FPS: {fps} | Theme: {theme_name}", (40, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255,255,255), 2)
        cv2.imshow("Hand-Tracking Mega-Controller", img)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'): break
        elif key == ord('t'): theme_idx = (theme_idx + 1) % len(themes)

    cap.release(); cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
