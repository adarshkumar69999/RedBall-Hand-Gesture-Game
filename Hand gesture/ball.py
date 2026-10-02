"""
Red Ball character with physics, squash/stretch deformation, and expressive animated eyes.
"""

import math
import random
import pygame

from config import (
    BALL_RADIUS, GRAVITY, BALL_ACCEL, BALL_MAX_SPEED, BALL_FRICTION,
    BALL_AIR_RESISTANCE, BALL_JUMP_FORCE, BOUNCE_PAD_FORCE, MAX_FALL_SPEED,
    COLOR_BALL_BASE, COLOR_BALL_SHADE, COLOR_BALL_HIGHLIGHT,
    COLOR_EYE_WHITE, COLOR_EYE_PUPIL
)


class RedBall:
    def __init__(self, start_x, start_y):
        self.spawn_x = float(start_x)
        self.spawn_y = float(start_y)
        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = 0.0
        self.vy = 0.0
        self.radius = BALL_RADIUS
        self.rotation_angle = 0.0  # Radians

        # Collision & status
        self.on_ground = False
        self.alive = True
        self.invulnerable_timer = 0

        # Squash & Stretch animation
        self.scale_x = 1.0
        self.scale_y = 1.0

        # Facial Animation
        self.blink_timer = random.randint(120, 240)
        self.is_blinking = False
        self.expression = "happy"  # "happy", "surprised", "neutral"

    def reset(self, x=None, y=None):
        if x is not None and y is not None:
            self.x, self.y = float(x), float(y)
        else:
            self.x, self.y = self.spawn_x, self.spawn_y
        self.vx = 0.0
        self.vy = 0.0
        self.rotation_angle = 0.0
        self.on_ground = False
        self.alive = True
        self.invulnerable_timer = 40
        self.scale_x = 1.0
        self.scale_y = 1.0

    def apply_input(self, steer_value, jump_requested, brake_requested, sound_manager=None, particle_system=None):
        """Processes steering (-1 to 1), jumping, and braking."""
        if not self.alive:
            return

        # Braking
        if brake_requested:
            self.vx *= 0.65
            if abs(self.vx) < 0.2:
                self.vx = 0.0
        else:
            # Steering acceleration
            if abs(steer_value) > 0.05:
                accel = BALL_ACCEL * steer_value
                self.vx += accel
                self.vx = max(-BALL_MAX_SPEED, min(BALL_MAX_SPEED, self.vx))

        # Jumping
        if jump_requested and self.on_ground:
            self.vy = BALL_JUMP_FORCE
            self.on_ground = False
            # Stretch vertically on jump
            self.scale_x = 0.8
            self.scale_y = 1.25
            if sound_manager:
                sound_manager.play("jump")
            if particle_system:
                particle_system.emit_dust(self.x, self.y + self.radius, count=5)

    def update(self, platforms, springs, hazards, sound_manager, particle_system):
        """Updates physics, platform collisions, hazards, and animations."""
        if not self.alive:
            return

        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        # Apply gravity
        self.vy += GRAVITY
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Apply friction
        friction = BALL_FRICTION if self.on_ground else BALL_AIR_RESISTANCE
        self.vx *= friction

        # Speed trail particles when rolling fast
        if abs(self.vx) > BALL_MAX_SPEED * 0.75 and particle_system:
            particle_system.emit_ball_trail(self.x, self.y, self.radius)

        # Move horizontally and resolve collisions
        self.x += self.vx
        self.rotation_angle += self.vx / self.radius
        self._resolve_horizontal_collisions(platforms)

        # Move vertically and resolve collisions
        self.y += self.vy
        was_on_ground = self.on_ground
        self.on_ground = False
        self._resolve_vertical_collisions(platforms, sound_manager, particle_system)

        # Check spring bounces
        self._check_springs(springs, sound_manager, particle_system)

        # Check hazard collisions (spikes / death pits)
        if self.invulnerable_timer <= 0:
            self._check_hazards(hazards, sound_manager, particle_system)

        # Ground rolling dust
        if self.on_ground and abs(self.vx) > 2.0 and random.random() < 0.25 and particle_system:
            particle_system.emit_dust(self.x, self.y + self.radius, count=1)

        # Update squash & stretch towards (1.0, 1.0)
        self.scale_x += (1.0 - self.scale_x) * 0.18
        self.scale_y += (1.0 - self.scale_y) * 0.18

        # Update face animations
        self._update_face()

    def _resolve_horizontal_collisions(self, platforms):
        for p in platforms:
            # Check AABB overlap with ball bounding box
            if (self.x + self.radius > p.rect.left and
                self.x - self.radius < p.rect.right and
                self.y + self.radius * 0.7 > p.rect.top and
                self.y - self.radius * 0.7 < p.rect.bottom):
                if self.vx > 0:
                    self.x = p.rect.left - self.radius
                    self.vx = 0
                elif self.vx < 0:
                    self.x = p.rect.right + self.radius
                    self.vx = 0

    def _resolve_vertical_collisions(self, platforms, sound_manager, particle_system):
        for p in platforms:
            if (self.x + self.radius * 0.7 > p.rect.left and
                self.x - self.radius * 0.7 < p.rect.right):
                # Falling onto platform top
                if self.vy > 0 and (self.y + self.radius >= p.rect.top) and (self.y - self.vy <= p.rect.top + 10):
                    self.y = p.rect.top - self.radius
                    if self.vy > 5.0 and particle_system:
                        # Squash on hard landing
                        self.scale_x = min(1.35, 1.0 + self.vy * 0.025)
                        self.scale_y = max(0.68, 1.0 - self.vy * 0.025)
                        particle_system.emit_dust(self.x, self.y + self.radius, count=4)
                    self.vy = 0
                    self.on_ground = True
                # Hitting ceiling
                elif self.vy < 0 and (self.y - self.radius <= p.rect.bottom) and (self.y - self.vy >= p.rect.bottom - 10):
                    self.y = p.rect.bottom + self.radius
                    self.vy = 0

    def _check_springs(self, springs, sound_manager, particle_system):
        for s in springs:
            if (self.x + self.radius * 0.6 > s.rect.left and
                self.x - self.radius * 0.6 < s.rect.right and
                self.y + self.radius >= s.rect.top and
                self.y - self.radius <= s.rect.bottom and
                self.vy > 0):
                self.vy = BOUNCE_PAD_FORCE
                self.scale_x = 0.7
                self.scale_y = 1.45
                s.trigger()
                if sound_manager:
                    sound_manager.play("bounce")
                if particle_system:
                    particle_system.emit_spring_burst(self.x, s.rect.top)

    def _check_hazards(self, hazards, sound_manager, particle_system):
        for h in hazards:
            # Distance check or rect collision
            if h.check_collision(self.x, self.y, self.radius):
                self.alive = False
                if sound_manager:
                    sound_manager.play("spike")
                if particle_system:
                    particle_system.emit_dust(self.x, self.y, count=12)
                break

    def _update_face(self):
        # Blinking logic
        self.blink_timer -= 1
        if self.blink_timer <= 0:
            if not self.is_blinking:
                self.is_blinking = True
                self.blink_timer = 7  # Duration of blink
            else:
                self.is_blinking = False
                self.blink_timer = random.randint(140, 280)

        # Expression
        if self.vy > 8.0:
            self.expression = "surprised"
        elif self.vy < -4.0 or abs(self.vx) > 4.0:
            self.expression = "happy"
        else:
            self.expression = "neutral"

    def draw(self, surface, camera_x, camera_y):
        """Draws the 3D-shaded Red Ball with animated facial expressions."""
        if not self.alive:
            return

        # Flicker if invulnerable
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 4) % 2 == 0:
            return

        draw_x = int(self.x - camera_x)
        draw_y = int(self.y - camera_y)

        rx = int(self.radius * self.scale_x)
        ry = int(self.radius * self.scale_y)

        # Ball shadow on ground
        if self.on_ground:
            shadow_rect = pygame.Rect(draw_x - rx + 4, draw_y + ry - 4, (rx - 4) * 2, 7)
            shadow_surf = pygame.Surface((shadow_rect.width, shadow_rect.height), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (30, 40, 50, 80), (0, 0, shadow_rect.width, shadow_rect.height))
            surface.blit(shadow_surf, shadow_rect)

        # 1. Base Ball Circle / Ellipse
        ball_rect = pygame.Rect(draw_x - rx, draw_y - ry, rx * 2, ry * 2)
        # Deep shaded rim
        pygame.draw.ellipse(surface, COLOR_BALL_SHADE, ball_rect)
        # Main body slightly inset
        inner_rect = pygame.Rect(draw_x - rx + 2, draw_y - ry + 1, rx * 2 - 4, ry * 2 - 3)
        pygame.draw.ellipse(surface, COLOR_BALL_BASE, inner_rect)

        # Specular Highlight (Light reflection on top-left)
        high_w = max(2, int(rx * 0.45))
        high_h = max(2, int(ry * 0.28))
        high_x = draw_x - int(rx * 0.45)
        high_y = draw_y - int(ry * 0.55)
        high_surf = pygame.Surface((high_w * 2, high_h * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(high_surf, (255, 255, 255, 140), (0, 0, high_w * 2, high_h * 2))
        surface.blit(high_surf, (high_x - high_w, high_y - high_h))

        # 2. Animated Eyes & Expression
        # Look direction offset based on velocity
        look_dx = max(-4, min(4, int(self.vx * 0.6)))
        look_dy = max(-3, min(3, int(self.vy * 0.3)))

        # Eye positions
        eye_y = draw_y - int(ry * 0.15)
        left_eye_x = draw_x - int(rx * 0.28) + look_dx
        right_eye_x = draw_x + int(rx * 0.24) + look_dx

        if self.is_blinking:
            # Draw closed eye slits
            pygame.draw.line(surface, COLOR_EYE_PUPIL, (left_eye_x - 3, eye_y), (left_eye_x + 3, eye_y), 2)
            pygame.draw.line(surface, COLOR_EYE_PUPIL, (right_eye_x - 3, eye_y), (right_eye_x + 3, eye_y), 2)
        else:
            eye_radius_x = max(2, int(rx * 0.22))
            eye_radius_y = max(3, int(ry * 0.30))

            # Left Eye White
            pygame.draw.ellipse(
                surface, COLOR_EYE_WHITE,
                (left_eye_x - eye_radius_x, eye_y - eye_radius_y + look_dy, eye_radius_x * 2, eye_radius_y * 2)
            )
            # Right Eye White
            pygame.draw.ellipse(
                surface, COLOR_EYE_WHITE,
                (right_eye_x - eye_radius_x, eye_y - eye_radius_y + look_dy, eye_radius_x * 2, eye_radius_y * 2)
            )

            # Pupils
            pupil_r = max(1, int(rx * 0.10))
            pupil_offset_x = max(-2, min(2, look_dx))
            pupil_offset_y = max(-2, min(2, look_dy))
            pygame.draw.circle(surface, COLOR_EYE_PUPIL, (left_eye_x + pupil_offset_x, eye_y + pupil_offset_y), pupil_r)
            pygame.draw.circle(surface, COLOR_EYE_PUPIL, (right_eye_x + pupil_offset_x, eye_y + pupil_offset_y), pupil_r)

        # 3. Mouth Expression
        mouth_y = draw_y + int(ry * 0.35)
        mouth_x = draw_x + look_dx // 2
        if self.expression == "happy":
            # Curved smile arc
            smile_rect = pygame.Rect(mouth_x - 6, mouth_y - 4, 12, 8)
            pygame.draw.arc(surface, COLOR_EYE_PUPIL, smile_rect, math.pi, 2 * math.pi, 2)
        elif self.expression == "surprised":
            # Little 'O' mouth
            pygame.draw.circle(surface, COLOR_EYE_PUPIL, (mouth_x, mouth_y), 3)
        else:
            # Small friendly line
            pygame.draw.line(surface, COLOR_EYE_PUPIL, (mouth_x - 4, mouth_y), (mouth_x + 4, mouth_y), 2)
