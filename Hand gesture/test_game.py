"""
Automated headless test suite for Hand Gesture Red Ball Game.
"""

import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

import unittest
import numpy as np
import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT, BALL_RADIUS
from level import Level, Platform, Star, Spike, BounceSpring, GoalFlag
from ball import RedBall
from particle import ParticleSystem
from sound_manager import SoundManager
from ui import UIManager
from hand_tracker import HandTracker


class TestRedBallGame(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    def setUp(self):
        self.sound_mgr = SoundManager()
        self.particles = ParticleSystem()
        self.ui_mgr = UIManager()

    def test_levels_construction(self):
        """Verifies all 3 levels initialize properly with platforms, stars, and goals."""
        for lvl_num in [1, 2, 3]:
            lvl = Level(lvl_num)
            self.assertGreater(len(lvl.platforms), 0, f"Level {lvl_num} has no platforms")
            self.assertGreater(len(lvl.stars), 0, f"Level {lvl_num} has no stars")
            self.assertIsNotNone(lvl.goal, f"Level {lvl_num} has no goal flag")
            self.assertGreater(lvl.total_stars, 0)
            
            # Run one update
            lvl.update()

    def test_ball_physics_and_jump(self):
        """Tests ball gravity, steering, jumping, and collision resolution."""
        lvl = Level(1)
        ball = RedBall(lvl.start_x, lvl.start_y)
        self.assertEqual(ball.x, lvl.start_x)
        self.assertEqual(ball.y, lvl.start_y)

        # Apply jump
        ball.on_ground = True
        ball.apply_input(steer_value=0.5, jump_requested=True, brake_requested=False, sound_manager=self.sound_mgr, particle_system=self.particles)
        self.assertLess(ball.vy, 0, "Ball should have negative vy on jump")
        self.assertGreater(ball.vx, 0, "Ball should have positive vx when steering right")

        # Simulate physics for 30 steps
        for _ in range(30):
            ball.update(lvl.platforms, lvl.springs, lvl.hazards, self.sound_mgr, self.particles)

        self.assertTrue(ball.alive, "Ball should be alive")

    def test_bounce_spring(self):
        """Tests bounce spring high launching mechanics."""
        spring = BounceSpring(200, 400)
        ball = RedBall(210, 390)
        ball.vy = 5.0  # Falling onto spring
        ball.update([], [spring], [], self.sound_mgr, self.particles)

        self.assertLess(ball.vy, -10.0, "Ball should launch upward after hitting spring")
        self.assertGreater(spring.compress_timer, 0, "Spring should be compressed")

    def test_star_collection(self):
        """Tests collectible star logic and count."""
        star = Star(200, 200)
        self.assertFalse(star.collected)
        collected = star.check_collection(200, 200, BALL_RADIUS)
        self.assertTrue(collected)
        self.assertTrue(star.collected)

    def test_spike_collision(self):
        """Tests spike hazard damage."""
        spike = Spike(200, 400)
        ball = RedBall(210, 390)
        ball.invulnerable_timer = 0
        ball.update([], [], [spike], self.sound_mgr, self.particles)
        self.assertFalse(ball.alive, "Ball should die when hitting spike")

    def test_particles(self):
        """Tests particle emission and lifecycle."""
        self.particles.emit_dust(100, 100, count=5)
        self.particles.emit_star_sparkles(200, 200, count=8)
        self.particles.emit_spring_burst(300, 300, count=6)
        self.assertGreater(len(self.particles.particles), 0)

        # Update until particles expire
        for _ in range(50):
            self.particles.update()

    def test_sound_manager(self):
        """Verifies all procedural sounds are synthesized and callable."""
        for sound_name in ["jump", "bounce", "star", "spike", "win", "checkpoint"]:
            self.assertIn(sound_name, self.sound_mgr.sounds)
            self.sound_mgr.play(sound_name)

    def test_ui_drawing(self):
        """Verifies UI rendering functions execute without exceptions."""
        surf = pygame.display.get_surface()
        self.ui_mgr.draw_background(surf, camera_x=100)
        self.ui_mgr.draw_hud(surf, lives=3, stars=2, total_stars=8, level_num=1, gesture_name="ROLL RIGHT", pip_surface=None)
        self.ui_mgr.draw_start_screen(surf)
        self.ui_mgr.draw_level_clear(surf, 1, 5, 5)
        self.ui_mgr.draw_game_over(surf)
        self.ui_mgr.draw_victory(surf)


if __name__ == "__main__":
    unittest.main()
