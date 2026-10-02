"""
Particle systems for visual effects (dust, sparkles, trails, shockwaves).
"""

import math
import random
import pygame


class Particle:
    def __init__(self, x, y, vx, vy, color, radius, lifetime, shrink=True, gravity=0.0):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.radius = float(radius)
        self.initial_radius = float(radius)
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.shrink = shrink
        self.gravity = gravity

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += self.gravity
        self.lifetime -= 1
        if self.shrink and self.max_lifetime > 0:
            self.radius = max(0.5, self.initial_radius * (self.lifetime / self.max_lifetime))
        return self.lifetime > 0

    def draw(self, surface, camera_x, camera_y):
        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)
        if self.radius > 0.5:
            pygame.draw.circle(surface, self.color, (draw_x, draw_y), int(self.radius))


class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit_dust(self, x, y, count=3):
        """Emits landing/rolling dust puffs."""
        for _ in range(count):
            vx = random.uniform(-1.5, 1.5)
            vy = random.uniform(-1.8, -0.2)
            shade = random.randint(180, 220)
            color = (shade, shade - 20, shade - 40)
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(3, 5), random.randint(14, 24), shrink=True, gravity=0.08))

    def emit_star_sparkles(self, x, y, count=16):
        """Emits radial golden starburst."""
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2.0, 5.5)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([
                (255, 220, 50),
                (255, 245, 160),
                (255, 255, 255),
                (255, 180, 30)
            ])
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(2.5, 4.5), random.randint(20, 35), shrink=True, gravity=0.12))

    def emit_spring_burst(self, x, y, count=12):
        """Emits energy sparks when bouncing on a spring."""
        for _ in range(count):
            angle = random.uniform(-math.pi * 0.85, -math.pi * 0.15)
            speed = random.uniform(3.0, 7.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([(255, 230, 80), (100, 240, 255), (255, 255, 255)])
            self.particles.append(Particle(x, y, vx, vy, color, random.uniform(3, 5), random.randint(16, 28), shrink=True, gravity=0.18))

    def emit_ball_trail(self, x, y, radius):
        """Emits faint motion trail when moving fast."""
        self.particles.append(Particle(x, y, 0, 0, (235, 80, 80), radius * 0.75, 10, shrink=True, gravity=0.0))

    def update(self):
        self.particles = [p for p in self.particles if p.update()]

    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            p.draw(surface, camera_x, camera_y)
