import cv2
import random
import math


class Particle:

    def __init__(self, x, y, base_color=None):
        self.x = float(x)
        self.y = float(y)

        angle  = random.uniform(0, 2 * math.pi)
        speed  = random.uniform(3, 11)

        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed - random.uniform(2, 5)   # slight upward bias
        self.gravity = 0.35

        self.radius = random.randint(3, 8)
        self.life   = random.randint(22, 38)
        self.max_life = self.life

        # Tint toward the fruit's own color, plus a bright pop
        if base_color:
            b, g, r = base_color
            self.color = (
                min(255, b + random.randint(20, 80)),
                min(255, g + random.randint(20, 80)),
                min(255, r + random.randint(20, 80)),
            )
        else:
            self.color = (
                random.randint(100, 255),
                random.randint(100, 255),
                random.randint(100, 255),
            )

    def update(self):
        self.x  += self.vx
        self.y  += self.vy
        self.vy += self.gravity   # gravity pull
        self.life -= 1

    def draw(self, frame):
        # Fade out as life decreases
        alpha = self.life / self.max_life
        faded = tuple(int(c * alpha) for c in self.color)
        r = max(1, int(self.radius * alpha))
        cv2.circle(frame, (int(self.x), int(self.y)), r, faded, -1, cv2.LINE_AA)

    def is_dead(self):
        return self.life <= 0