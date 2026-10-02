"""
Main game loop and state manager for Red Ball: Hand Gesture Adventure.
"""

import os
import sys

# Ensure current working directory is the script's directory regardless of how VS Code launches it
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE,
    COLOR_BG_BOTTOM
)
from hand_tracker import HandTracker
from sound_manager import SoundManager
from particle import ParticleSystem
from ball import RedBall
from level import Level
from ui import UIManager

# Game States
STATE_START = "START"
STATE_PLAYING = "PLAYING"
STATE_LEVEL_CLEAR = "LEVEL_CLEAR"
STATE_GAME_OVER = "GAME_OVER"
STATE_VICTORY = "VICTORY"
STATE_PAUSED = "PAUSED"


class Game:
    def __init__(self):
        print("==================================================")
        print("    RED BALL: HAND GESTURE ADVENTURE (v1.1)       ")
        print("==================================================")
        print(f"[Game] Working Directory: {os.getcwd()}")

        pygame.init()
        pygame.display.set_caption(TITLE)
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()

        # Subsystems
        self.hand_tracker = HandTracker()
        print(f"[Game] Camera Status: {self.hand_tracker.status_message}")
        print("==================================================")

        self.sound_manager = SoundManager()
        self.particle_system = ParticleSystem()
        self.ui_manager = UIManager()

        # Game State
        self.state = STATE_START
        self.current_level_num = 1
        self.max_levels = 3
        self.lives = 3
        self.collected_stars = 0

        # Load initial level and ball
        self.level = Level(self.current_level_num)
        self.ball = RedBall(self.level.start_x, self.level.start_y)

        # Smooth Camera Tracking
        self.camera_x = 0.0
        self.camera_y = 0.0

        self.running = True

    def reset_level(self, keep_lives=False):
        """Resets the current level."""
        if not keep_lives:
            self.lives = 3
        self.level = Level(self.current_level_num)
        self.ball.reset(self.level.start_x, self.level.start_y)
        self.collected_stars = 0
        self.camera_x = max(0, self.ball.x - 300)

    def next_level(self):
        """Advances to the next level or victory."""
        if self.current_level_num < self.max_levels:
            self.current_level_num += 1
            self.reset_level(keep_lives=True)
            self.state = STATE_PLAYING
        else:
            self.state = STATE_VICTORY
            self.sound_manager.play("win")

    def run(self):
        """Main game loop."""
        while self.running:
            self.clock.tick(FPS)
            self._handle_events()
            self._update()
            self._draw()

        self._cleanup()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING
                elif event.key == pygame.K_c:
                    self.ui_manager.toggle_pip()
                elif event.key == pygame.K_r:
                    if self.state in [STATE_GAME_OVER, STATE_VICTORY]:
                        self.current_level_num = 1
                        self.reset_level()
                        self.state = STATE_PLAYING
                elif event.key == pygame.K_SPACE:
                    if self.state == STATE_START:
                        self.state = STATE_PLAYING
                    elif self.state == STATE_LEVEL_CLEAR:
                        self.next_level()
                    elif self.state == STATE_VICTORY:
                        self.current_level_num = 1
                        self.reset_level()
                        self.state = STATE_PLAYING

    def _update(self):
        # Always update vision hand tracking
        self.hand_tracker.update()

        # Keyboard input polling
        keys = pygame.key.get_pressed()
        kb_steer = 0.0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            kb_steer -= 1.0
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            kb_steer += 1.0

        kb_jump = keys[pygame.K_SPACE] or keys[pygame.K_UP] or keys[pygame.K_w]
        kb_brake = keys[pygame.K_DOWN] or keys[pygame.K_s]

        # Combine Vision & Keyboard inputs
        active_steer = kb_steer if abs(kb_steer) > 0.01 else self.hand_tracker.steer_value
        active_jump = kb_jump or self.hand_tracker.is_jumping
        active_brake = kb_brake or self.hand_tracker.is_braking

        # State specific updates
        if self.state == STATE_START:
            # Can start with jump gesture as well
            if self.hand_tracker.is_jumping:
                self.state = STATE_PLAYING

        elif self.state == STATE_LEVEL_CLEAR:
            if self.hand_tracker.is_jumping:
                self.next_level()

        elif self.state == STATE_GAME_OVER:
            if self.hand_tracker.is_jumping:
                self.current_level_num = 1
                self.reset_level()
                self.state = STATE_PLAYING

        elif self.state == STATE_PLAYING:
            # Apply controls to Red Ball
            self.ball.apply_input(
                active_steer, active_jump, active_brake,
                self.sound_manager, self.particle_system
            )

            # Update level elements (moving platforms, etc.)
            self.level.update()

            # Update Ball physics & collisions
            self.ball.update(
                self.level.platforms,
                self.level.springs,
                self.level.hazards,
                self.sound_manager,
                self.particle_system
            )

            # Collect stars
            for star in self.level.stars:
                if star.check_collection(self.ball.x, self.ball.y, self.ball.radius):
                    self.collected_stars += 1
                    self.sound_manager.play("star")
                    self.particle_system.emit_star_sparkles(star.x, star.y)

            # Check level goal reached
            if self.level.goal and self.level.goal.check_collision(self.ball.x, self.ball.y, self.ball.radius):
                self.sound_manager.play("win")
                self.state = STATE_LEVEL_CLEAR

            # Handle ball death (hit spike or fell off)
            if not self.ball.alive:
                self.lives -= 1
                if self.lives > 0:
                    self.ball.reset(self.level.start_x, self.level.start_y)
                else:
                    self.state = STATE_GAME_OVER

            # Update particles
            self.particle_system.update()

            # Smooth Camera Lerping (Follow Ball)
            target_cam_x = self.ball.x - SCREEN_WIDTH * 0.35
            target_cam_x = max(0, min(self.level.level_width - SCREEN_WIDTH, target_cam_x))
            self.camera_x += (target_cam_x - self.camera_x) * 0.08

    def _draw(self):
        # Draw parallax background
        self.ui_manager.draw_background(self.screen, self.camera_x)

        if self.state in [STATE_PLAYING, STATE_PAUSED, STATE_LEVEL_CLEAR]:
            # Draw game world
            self.level.draw(self.screen, self.camera_x, self.camera_y)
            self.particle_system.draw(self.screen, self.camera_x, self.camera_y)
            self.ball.draw(self.screen, self.camera_x, self.camera_y)

            # Draw HUD
            self.ui_manager.draw_hud(
                self.screen,
                self.lives,
                self.collected_stars,
                self.level.total_stars,
                self.current_level_num,
                self.hand_tracker.gesture_name,
                self.hand_tracker.pip_surface
            )

            if self.state == STATE_LEVEL_CLEAR:
                self.ui_manager.draw_level_clear(
                    self.screen, self.current_level_num, self.collected_stars, self.level.total_stars
                )
            elif self.state == STATE_PAUSED:
                # Dim overlay
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                self.screen.blit(overlay, (0, 0))
                pause_txt = self.ui_manager.font_large.render("PAUSED (Press ESC to Resume)", True, (255, 255, 255))
                self.screen.blit(pause_txt, (SCREEN_WIDTH // 2 - pause_txt.get_width() // 2, SCREEN_HEIGHT // 2))

        elif self.state == STATE_START:
            self.ui_manager.draw_start_screen(self.screen, self.hand_tracker.pip_surface)

        elif self.state == STATE_GAME_OVER:
            self.ui_manager.draw_game_over(self.screen)

        elif self.state == STATE_VICTORY:
            self.ui_manager.draw_victory(self.screen)

        pygame.display.flip()

    def _cleanup(self):
        self.hand_tracker.close()
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
