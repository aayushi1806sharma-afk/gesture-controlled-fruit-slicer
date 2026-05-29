import cv2
import random
import math
import numpy as np


# ────────────────────────────────────────────────────────
#  FRUIT DEFINITIONS  (shape, colors, label)
# ────────────────────────────────────────────────────────
FRUIT_CONFIGS = [
    # name,       body_color (BGR),    shine_color,       shape
    ("Apple",     (40,  60, 220),      (120, 120, 255),   "circle"),
    ("Banana",    (0,  210, 255),      (100, 240, 255),   "crescent"),
    ("Watermelon",(50, 180,  60),      (120, 220, 100),   "circle"),
    ("Orange",    (0,  140, 255),      (100, 200, 255),   "circle"),
    ("Mango",     (0,  200, 220),      (120, 240, 255),   "oval"),
    ("Grape",     (180,  40, 130),     (220, 120, 200),   "circle"),
    ("Kiwi",      (30, 140,  80),      (100, 200, 130),   "circle"),
    ("Lemon",     (0,  230, 240),      (100, 255, 255),   "oval"),
]


def _draw_circle_fruit(frame, cx, cy, r, body_color, shine_color):
    """Filled anti-aliased circle + shine dot + tiny stem."""
    cv2.circle(frame, (cx, cy), r, body_color, -1, cv2.LINE_AA)
    # Dark edge ring
    cv2.circle(frame, (cx, cy), r, tuple(max(0, c - 60) for c in body_color), 2, cv2.LINE_AA)
    # Shine
    sx, sy = cx - r // 3, cy - r // 3
    cv2.circle(frame, (sx, sy), r // 5, shine_color, -1, cv2.LINE_AA)
    # Stem
    cv2.line(frame, (cx, cy - r), (cx + 4, cy - r - 10), (30, 100, 30), 3, cv2.LINE_AA)


def _draw_oval_fruit(frame, cx, cy, r, body_color, shine_color):
    """Ellipse for mango / lemon style."""
    axes = (r, int(r * 0.7))
    cv2.ellipse(frame, (cx, cy), axes, 20, 0, 360, body_color, -1, cv2.LINE_AA)
    cv2.ellipse(frame, (cx, cy), axes, 20, 0, 360,
                tuple(max(0, c - 50) for c in body_color), 2, cv2.LINE_AA)
    sx, sy = cx - axes[0] // 3, cy - axes[1] // 3
    cv2.circle(frame, (sx, sy), r // 5, shine_color, -1, cv2.LINE_AA)
    cv2.line(frame, (cx, cy - axes[1]), (cx + 4, cy - axes[1] - 10), (30, 100, 30), 3, cv2.LINE_AA)


def _draw_crescent_fruit(frame, cx, cy, r, body_color, shine_color):
    """Crescent-moon shape for banana."""
    pts = []
    for a in range(0, 181):
        rad = math.radians(a)
        px = int(cx + r * math.cos(rad))
        py = int(cy - int(r * 0.5) * math.sin(rad))
        pts.append([px, py])
    for a in range(180, -1, -1):
        rad = math.radians(a)
        px = int(cx + int(r * 0.6) * math.cos(rad))
        py = int(cy - int(r * 0.3) * math.sin(rad))
        pts.append([px, py])
    pts = np.array(pts, dtype=np.int32)
    cv2.fillPoly(frame, [pts], body_color, cv2.LINE_AA)
    cv2.polylines(frame, [pts], True,
                  tuple(max(0, c - 60) for c in body_color), 2, cv2.LINE_AA)
    cv2.circle(frame, (cx - r // 3, cy - r // 5), r // 6, shine_color, -1, cv2.LINE_AA)


def draw_fruit(frame, cx, cy, r, body_color, shine_color, shape):
    if shape == "circle":
        _draw_circle_fruit(frame, cx, cy, r, body_color, shine_color)
    elif shape == "oval":
        _draw_oval_fruit(frame, cx, cy, r, body_color, shine_color)
    elif shape == "crescent":
        _draw_crescent_fruit(frame, cx, cy, r, body_color, shine_color)
    else:
        _draw_circle_fruit(frame, cx, cy, r, body_color, shine_color)


# ────────────────────────────────────────────────────────
#  VEGETABLE  (fruit to slice)
# ────────────────────────────────────────────────────────
class Vegetable:
    def __init__(self):
        self.x = random.randint(100, 1180)
        self.y = random.randint(-150, -50)
        self.speed = random.randint(4, 8)
        self.radius = 38
        self.spin = 0
        self.spin_speed = random.uniform(-3, 3)

        cfg = random.choice(FRUIT_CONFIGS)
        self.name, self.body_color, self.shine_color, self.shape = cfg

    def update(self):
        self.y += self.speed
        self.spin += self.spin_speed

    def draw(self, frame):
        draw_fruit(frame, self.x, self.y, self.radius,
                   self.body_color, self.shine_color, self.shape)

    def check_slice(self, finger_pos):
        if not finger_pos:
            return False
        fx, fy = finger_pos
        return math.hypot(self.x - fx, self.y - fy) < self.radius + 10


# ────────────────────────────────────────────────────────
#  BOMB
# ────────────────────────────────────────────────────────
class Bomb:
    def __init__(self):
        self.x = random.randint(100, 1180)
        self.y = random.randint(-150, -50)
        self.speed = random.randint(5, 9)
        self.radius = 35
        self.pulse = 0          # for animated fuse glow

    def update(self):
        self.y += self.speed
        self.pulse = (self.pulse + 5) % 360

    def draw(self, frame):
        cx, cy = self.x, self.y
        r = self.radius

        # ── Body ──
        cv2.circle(frame, (cx, cy), r, (30, 30, 30), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx, cy), r, (80, 80, 80), 2, cv2.LINE_AA)

        # ── Shine ──
        cv2.circle(frame, (cx - r // 3, cy - r // 3), r // 5, (100, 100, 100), -1, cv2.LINE_AA)

        # ── Skull face ──
        eye_r = r // 6
        # Eyes
        cv2.circle(frame, (cx - r // 3, cy - r // 5), eye_r, (0, 0, 220), -1, cv2.LINE_AA)
        cv2.circle(frame, (cx + r // 3, cy - r // 5), eye_r, (0, 0, 220), -1, cv2.LINE_AA)
        # Mouth (arc)
        cv2.ellipse(frame, (cx, cy + r // 5), (r // 3, r // 5),
                    0, 0, 180, (0, 0, 200), 2, cv2.LINE_AA)

        # ── Fuse ──
        fuse_x, fuse_y = cx + r // 2, cy - r
        tip_x = fuse_x + 6
        tip_y = fuse_y - 14
        cv2.line(frame, (fuse_x, fuse_y), (tip_x, tip_y), (60, 60, 180), 3, cv2.LINE_AA)

        # Animated spark at fuse tip
        glow = int(180 + 75 * math.sin(math.radians(self.pulse)))
        cv2.circle(frame, (tip_x, tip_y), 6, (0, glow, 255), -1, cv2.LINE_AA)
        cv2.circle(frame, (tip_x, tip_y), 9, (0, glow // 2, 180), 2, cv2.LINE_AA)

    def check_hit(self, finger_pos):
        if not finger_pos:
            return False
        fx, fy = finger_pos
        return math.hypot(self.x - fx, self.y - fy) < self.radius