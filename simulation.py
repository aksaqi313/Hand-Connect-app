import numpy as np
import cv2
import random
import time

class Theme:
    RAINBOW = "Rainbow"
    CYBERPUNK = "Cyberpunk"
    LAVA = "Lava"
    OCEAN = "Ocean"
    GALAXY = "Galaxy"

    @staticmethod
    def get_color(theme_name, t, index, total):
        if theme_name == Theme.RAINBOW:
            hue = int((t * 100 + index * (180 / total)) % 180) # OpenCV uses 0-179 for Hue
            img_hsv = np.uint8([[[hue, 255, 255]]])
            img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
            return tuple(map(int, img_rgb[0][0]))
        
        elif theme_name == Theme.CYBERPUNK:
            return (60, 0, 255) if index % 2 == 0 else (255, 240, 0) # BGR
        
        elif theme_name == Theme.LAVA:
            hue = int((10 + (index * 5)) % 20)
            val = int(127 + np.sin(t) * 50)
            img_hsv = np.uint8([[[hue, 255, val]]])
            img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
            return tuple(map(int, img_rgb[0][0]))
        
        elif theme_name == Theme.OCEAN:
            hue = int((90 + (index * 10)) % 120)
            img_hsv = np.uint8([[[hue, 255, 200]]])
            img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
            return tuple(map(int, img_rgb[0][0]))
        
        elif theme_name == Theme.GALAXY:
            hue = int((130 + np.sin(t * 2 + index) * 20) % 180)
            img_hsv = np.uint8([[[hue, 150, 200]]])
            img_rgb = cv2.cvtColor(img_hsv, cv2.COLOR_HSV2BGR)
            return tuple(map(int, img_rgb[0][0]))
        
        return (255, 255, 255)

class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx = (random.random() - 0.5) * 15
        self.vy = (random.random() - 0.5) * 15
        self.life = 1.0
        self.color = color
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.3 # Gravity
        self.life -= 0.03
        return self.life > 0

    def draw(self, img):
        alpha = self.life
        color = tuple(map(lambda x: int(x * alpha), self.color))
        cv2.circle(img, (int(self.x), int(self.y)), self.size, color, -1)

class Ripple:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.radius = 0
        self.max_radius = random.randint(100, 200)
        self.life = 1.0
        self.color = color

    def update(self):
        self.radius += (self.max_radius - self.radius) * 0.15
        self.life -= 0.04
        return self.life > 0

    def draw(self, img):
        thickness = int(4 * self.life)
        if thickness < 1: thickness = 1
        cv2.circle(img, (int(self.x), int(self.y)), int(self.radius), self.color, thickness)

class MatrixEffect:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.font_size = 18
        self.columns = width // self.font_size
        self.drops = [random.random() * height/self.font_size for _ in range(self.columns)]

    def draw(self, img, theme_color, hand_vel):
        speed_mult = 1.0 + (hand_vel * 2.0)
        for i in range(len(self.drops)):
            if random.random() > 0.95:
                char = chr(random.randint(0x30A0, 0x30FF)) # Katakana
                x = i * self.font_size
                y = int(self.drops[i] * self.font_size)
                if y < self.height:
                    cv2.putText(img, char, (x, y), cv2.FONT_HERSHEY_PLAIN, 1.2, theme_color, 1)
            
            self.drops[i] += random.random() * speed_mult
            if self.drops[i] * self.font_size > self.height and random.random() > 0.9:
                self.drops[i] = 0
