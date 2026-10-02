"""
Level elements and layouts: platforms, moving platforms, collectible stars,
spikes, bounce springs, checkpoints, and goal flags.
"""

import math
import pygame

from config import (
    COLOR_GRASS, COLOR_GRASS_TOP, COLOR_DIRT, COLOR_WOOD,
    COLOR_SPIKE, COLOR_SPIKE_TIP, COLOR_STAR, COLOR_STAR_OUTLINE, COLOR_STAR_GLOW,
    COLOR_SPRING_BASE, COLOR_SPRING_COIL, COLOR_FLAG_POLE, COLOR_FLAG_RED, COLOR_FLAG_GOLD
)


class Platform:
    def __init__(self, x, y, width, height, is_moving=False, move_range=0, move_speed=0.03, horizontal=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.initial_x = x
        self.initial_y = y
        self.is_moving = is_moving
        self.move_range = move_range
        self.move_speed = move_speed
        self.horizontal = horizontal
        self.phase = 0.0

    def update(self):
        if self.is_moving and self.move_range > 0:
            self.phase += self.move_speed
            offset = math.sin(self.phase) * self.move_range
            if self.horizontal:
                self.rect.x = int(self.initial_x + offset)
            else:
                self.rect.y = int(self.initial_y + offset)

    def draw(self, surface, camera_x, camera_y):
        draw_rect = pygame.Rect(
            self.rect.x - camera_x,
            self.rect.y - camera_y,
            self.rect.width,
            self.rect.height
        )

        if self.is_moving:
            # Wooden floating platform
            pygame.draw.rect(surface, COLOR_WOOD, draw_rect, border_radius=4)
            pygame.draw.rect(surface, (200, 150, 90), (draw_rect.x, draw_rect.y, draw_rect.width, 4), border_radius=2)
            pygame.draw.rect(surface, (100, 65, 30), draw_rect, width=2, border_radius=4)
        else:
            # Grass & dirt ground
            # Dirt bottom
            pygame.draw.rect(surface, COLOR_DIRT, draw_rect)
            # Grass surface
            grass_h = min(12, self.rect.height)
            grass_rect = pygame.Rect(draw_rect.x, draw_rect.y, draw_rect.width, grass_h)
            pygame.draw.rect(surface, COLOR_GRASS, grass_rect)
            pygame.draw.line(surface, COLOR_GRASS_TOP, (draw_rect.left, draw_rect.top), (draw_rect.right, draw_rect.top), 3)


class Star:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.base_y = float(y)
        self.radius = 16
        self.collected = False
        self.angle = 0.0

    def update(self):
        if not self.collected:
            self.angle += 0.05
            self.y = self.base_y + math.sin(self.angle * 1.5) * 5.0

    def check_collection(self, ball_x, ball_y, ball_radius):
        if self.collected:
            return False
        dist = math.hypot(self.x - ball_x, self.y - ball_y)
        if dist < self.radius + ball_radius:
            self.collected = True
            return True
        return False

    def draw(self, surface, camera_x, camera_y):
        if self.collected:
            return

        cx = int(self.x - camera_x)
        cy = int(self.y - camera_y)

        # Pulse glow
        glow_size = int(self.radius * (1.2 + 0.15 * math.sin(self.angle * 3)))
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 240, 120, 60), (glow_size, glow_size), glow_size)
        surface.blit(glow_surf, (cx - glow_size, cy - glow_size))

        # Draw 5-pointed star
        points = []
        for i in range(10):
            r = self.radius if i % 2 == 0 else self.radius * 0.45
            a = self.angle + i * math.pi / 5.0 - math.pi / 2.0
            points.append((cx + math.cos(a) * r, cy + math.sin(a) * r))

        pygame.draw.polygon(surface, COLOR_STAR, points)
        pygame.draw.polygon(surface, COLOR_STAR_OUTLINE, points, 2)


class Spike:
    def __init__(self, x, y, width=32, height=24):
        self.rect = pygame.Rect(x, y - height, width, height)
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def check_collision(self, ball_x, ball_y, ball_radius):
        # Slightly generous hitbox for fair gameplay
        margin = 4
        return (
            ball_x + ball_radius - margin > self.rect.left and
            ball_x - ball_radius + margin < self.rect.right and
            ball_y + ball_radius - margin > self.rect.top and
            ball_y - ball_radius + margin < self.rect.bottom
        )

    def draw(self, surface, camera_x, camera_y):
        cx = self.rect.x - camera_x
        cy = self.rect.bottom - camera_y
        tip_x = cx + self.width // 2
        tip_y = self.rect.top - camera_y

        pts = [(cx, cy), (tip_x, tip_y), (cx + self.width, cy)]
        pygame.draw.polygon(surface, COLOR_SPIKE, pts)
        # Highlight edge
        pygame.draw.line(surface, COLOR_SPIKE_TIP, (cx, cy), (tip_x, tip_y), 2)
        pygame.draw.line(surface, (90, 90, 100), (tip_x, tip_y), (cx + self.width, cy), 1)


class BounceSpring:
    def __init__(self, x, y, width=40, height=22):
        self.rect = pygame.Rect(x, y - height, width, height)
        self.base_y = y
        self.compress_timer = 0

    def trigger(self):
        self.compress_timer = 12

    def update(self):
        if self.compress_timer > 0:
            self.compress_timer -= 1

    def draw(self, surface, camera_x, camera_y):
        bx = self.rect.x - camera_x
        by = self.rect.y - camera_y
        w = self.rect.width
        h = self.rect.height

        # Base plate
        pygame.draw.rect(surface, COLOR_SPRING_BASE, (bx, by + h - 6, w, 6), border_radius=2)

        # Spring coils
        coil_h = h - 6
        if self.compress_timer > 0:
            coil_h = int(coil_h * 0.45)

        coils = 4
        prev_pt = (bx + 6, by + h - 6)
        for i in range(1, coils + 1):
            px = bx + w - 6 if i % 2 == 1 else bx + 6
            py = by + h - 6 - int((coil_h / coils) * i)
            pygame.draw.line(surface, COLOR_SPRING_COIL, prev_pt, (px, py), 3)
            prev_pt = (px, py)

        # Top cap
        pygame.draw.rect(surface, (220, 60, 60), (bx + 2, by + h - 6 - coil_h - 4, w - 4, 5), border_radius=2)


class GoalFlag:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 40
        self.height = 80
        self.rect = pygame.Rect(x, y - self.height, self.width, self.height)
        self.wave_phase = 0.0

    def check_collision(self, ball_x, ball_y, ball_radius):
        return (
            ball_x + ball_radius > self.rect.left and
            ball_x - ball_radius < self.rect.right and
            ball_y + ball_radius > self.rect.top and
            ball_y - ball_radius < self.rect.bottom
        )

    def update(self):
        self.wave_phase += 0.08

    def draw(self, surface, camera_x, camera_y):
        bx = self.x - camera_x
        by = self.y - camera_y

        # Pole
        pygame.draw.line(surface, COLOR_FLAG_POLE, (bx, by), (bx, by - self.height), 4)
        # Gold ball on top of pole
        pygame.draw.circle(surface, COLOR_FLAG_GOLD, (bx, by - self.height), 6)

        # Waving flag triangle
        wave = math.sin(self.wave_phase) * 5.0
        flag_pts = [
            (bx + 2, by - self.height + 4),
            (bx + 34 + wave, by - self.height + 18),
            (bx + 2, by - self.height + 32)
        ]
        pygame.draw.polygon(surface, COLOR_FLAG_RED, flag_pts)
        pygame.draw.polygon(surface, COLOR_FLAG_GOLD, flag_pts, 2)


class PitHazard:
    """Kills ball if it falls below the map."""
    def __init__(self, death_y=850):
        self.death_y = death_y

    def check_collision(self, ball_x, ball_y, ball_radius):
        return ball_y - ball_radius > self.death_y


class Level:
    def __init__(self, level_num=1):
        self.level_num = level_num
        self.platforms = []
        self.stars = []
        self.spikes = []
        self.springs = []
        self.hazards = [PitHazard(death_y=850)]
        self.goal = None
        self.start_x = 100
        self.start_y = 480
        self.total_stars = 0
        self.level_width = 3000

        self._build_level()

    def _build_level(self):
        if self.level_num == 1:
            self._build_level_1()
        elif self.level_num == 2:
            self._build_level_2()
        else:
            self._build_level_3()
        self.total_stars = len(self.stars)

    def _build_level_1(self):
        """Level 1: Rolling Meadows - Basics, stars, gentle jumps, springs."""
        self.start_x = 120
        self.start_y = 480
        self.level_width = 3200

        # Start ground
        self.platforms.append(Platform(0, 560, 650, 160))

        # Stars over start
        self.stars.append(Star(300, 500))
        self.stars.append(Star(420, 500))

        # First gap with small island
        self.platforms.append(Platform(760, 540, 220, 180))
        self.stars.append(Star(870, 470))

        # Spring pad that vaults to high cliff
        self.platforms.append(Platform(1070, 560, 280, 160))
        self.springs.append(BounceSpring(1220, 560))

        # High cliff
        self.platforms.append(Platform(1380, 360, 480, 360))
        self.stars.append(Star(1460, 300))
        self.stars.append(Star(1620, 290))
        self.stars.append(Star(1780, 300))

        # Step down with single spike
        self.platforms.append(Platform(1940, 460, 360, 260))
        self.spikes.append(Spike(2100, 460))
        self.stars.append(Star(2116, 380))

        # Moving platform over pit
        self.platforms.append(Platform(2380, 460, 140, 24, is_moving=True, move_range=120, move_speed=0.035, horizontal=True))
        self.stars.append(Star(2450, 380))

        # Final stretch and goal
        self.platforms.append(Platform(2700, 520, 500, 200))
        self.stars.append(Star(2850, 460))
        self.goal = GoalFlag(3050, 520)

    def _build_level_2(self):
        """Level 2: The Spiked Valley - Moving platforms, precision timing."""
        self.start_x = 100
        self.start_y = 480
        self.level_width = 3600

        # Starting platform
        self.platforms.append(Platform(0, 560, 450, 160))
        self.stars.append(Star(250, 490))

        # Moving elevator platform
        self.platforms.append(Platform(520, 460, 140, 24, is_moving=True, move_range=100, move_speed=0.04, horizontal=False))
        self.stars.append(Star(590, 320))

        # Upper ledge with spikes
        self.platforms.append(Platform(760, 380, 400, 340))
        self.spikes.append(Spike(860, 380))
        self.spikes.append(Spike(980, 380))
        self.stars.append(Star(920, 300))

        # Drop down to spring launcher
        self.platforms.append(Platform(1240, 580, 300, 140))
        self.springs.append(BounceSpring(1380, 580))

        # Floating high islands
        self.platforms.append(Platform(1550, 300, 180, 24))
        self.stars.append(Star(1640, 230))

        self.platforms.append(Platform(1830, 280, 140, 24, is_moving=True, move_range=110, move_speed=0.045, horizontal=True))
        self.stars.append(Star(1900, 200))

        # Middle checkpoint island
        self.platforms.append(Platform(2180, 440, 380, 280))
        self.spikes.append(Spike(2300, 440))
        self.stars.append(Star(2316, 360))

        # Double moving platforms
        self.platforms.append(Platform(2650, 460, 120, 24, is_moving=True, move_range=90, move_speed=0.05, horizontal=True))
        self.platforms.append(Platform(2900, 400, 120, 24, is_moving=True, move_range=80, move_speed=0.04, horizontal=False))
        self.stars.append(Star(2960, 280))

        # Final summit and goal
        self.platforms.append(Platform(3150, 480, 450, 240))
        self.stars.append(Star(3300, 420))
        self.goal = GoalFlag(3450, 480)

    def _build_level_3(self):
        """Level 3: Cloud Peaks - Grand challenge, high jumps, golden trophy."""
        self.start_x = 100
        self.start_y = 480
        self.level_width = 3800

        self.platforms.append(Platform(0, 560, 400, 160))
        self.springs.append(BounceSpring(300, 560))

        # High sky step
        self.platforms.append(Platform(460, 300, 180, 24))
        self.stars.append(Star(550, 230))

        # Rapid moving platform
        self.platforms.append(Platform(720, 300, 120, 24, is_moving=True, move_range=120, move_speed=0.06, horizontal=True))
        self.stars.append(Star(780, 220))

        # Floating spiked fortress
        self.platforms.append(Platform(1050, 360, 520, 360))
        self.spikes.append(Spike(1150, 360))
        self.spikes.append(Spike(1210, 360))
        self.spikes.append(Spike(1380, 360))
        self.stars.append(Star(1280, 280))

        # Super spring launcher
        self.platforms.append(Platform(1650, 520, 240, 200))
        self.springs.append(BounceSpring(1760, 520))

        # Sky clouds
        self.platforms.append(Platform(1950, 240, 150, 24))
        self.stars.append(Star(2020, 170))

        self.platforms.append(Platform(2200, 260, 140, 24, is_moving=True, move_range=110, move_speed=0.045, horizontal=False))
        self.stars.append(Star(2270, 160))

        self.platforms.append(Platform(2450, 320, 160, 24))
        self.stars.append(Star(2530, 250))

        # Final spike bridge
        self.platforms.append(Platform(2720, 460, 550, 260))
        self.spikes.append(Spike(2840, 460))
        self.spikes.append(Spike(2940, 460))
        self.stars.append(Star(2890, 380))

        # Goal platform
        self.platforms.append(Platform(3350, 440, 450, 280))
        self.stars.append(Star(3500, 370))
        self.goal = GoalFlag(3650, 440)

    def update(self):
        for p in self.platforms:
            p.update()
        for s in self.stars:
            s.update()
        for sp in self.springs:
            sp.update()
        if self.goal:
            self.goal.update()

    def draw(self, surface, camera_x, camera_y):
        for p in self.platforms:
            p.draw(surface, camera_x, camera_y)
        for sp in self.springs:
            sp.draw(surface, camera_x, camera_y)
        for h in self.spikes:
            h.draw(surface, camera_x, camera_y)
        for s in self.stars:
            s.draw(surface, camera_x, camera_y)
        if self.goal:
            self.goal.draw(surface, camera_x, camera_y)
