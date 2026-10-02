"""
UI Manager: HUD, Picture-in-Picture camera view, parallax backgrounds,
and game state screens (Start, Pause, Victory, Game Over).
"""

import math
import pygame

from config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_TOP, COLOR_BG_BOTTOM,
    COLOR_UI_TEXT, COLOR_UI_SHADOW, COLOR_HUD_PANEL, COLOR_ACCENT,
    COLOR_STAR, COLOR_BALL_BASE
)


class Cloud:
    def __init__(self, x, y, width, speed):
        self.x = float(x)
        self.y = float(y)
        self.width = width
        self.height = int(width * 0.45)
        self.speed = speed

    def update(self):
        self.x += self.speed
        if self.x > SCREEN_WIDTH + 150:
            self.x = -self.width - 50

    def draw(self, surface):
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # Draw fluffy overlapping ellipses
        r = self.height // 2
        pygame.draw.ellipse(surf, (255, 255, 255, 170), (0, r // 2, self.width, r))
        pygame.draw.circle(surf, (255, 255, 255, 190), (int(self.width * 0.35), r), int(r * 0.9))
        pygame.draw.circle(surf, (255, 255, 255, 210), (int(self.width * 0.6), r), int(r * 1.1))
        surface.blit(surf, (int(self.x), int(self.y)))


class UIManager:
    def __init__(self):
        pygame.font.init()
        # Fonts
        self.font_title = pygame.font.SysFont("Arial", 46, bold=True)
        self.font_large = pygame.font.SysFont("Arial", 32, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 22, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 16, bold=True)

        # Clouds for parallax background
        self.clouds = [
            Cloud(100, 70, 160, 0.4),
            Cloud(500, 120, 220, 0.25),
            Cloud(900, 60, 180, 0.35),
            Cloud(1300, 140, 260, 0.2)
        ]

        self.show_pip = True

    def toggle_pip(self):
        self.show_pip = not self.show_pip

    def draw_background(self, surface, camera_x):
        """Draws sky gradient and parallax mountain/hill silhouettes."""
        # 1. Sky Gradient
        for y in range(0, SCREEN_HEIGHT, 4):
            factor = y / SCREEN_HEIGHT
            r = int(COLOR_BG_TOP[0] * (1 - factor) + COLOR_BG_BOTTOM[0] * factor)
            g = int(COLOR_BG_TOP[1] * (1 - factor) + COLOR_BG_BOTTOM[1] * factor)
            b = int(COLOR_BG_TOP[2] * (1 - factor) + COLOR_BG_BOTTOM[2] * factor)
            pygame.draw.rect(surface, (r, g, b), (0, y, SCREEN_WIDTH, 4))

        # 2. Clouds
        for c in self.clouds:
            c.update()
            c.draw(surface)

        # 3. Far Mountains (Slow parallax: 0.15)
        far_offset = int(camera_x * 0.12) % SCREEN_WIDTH
        self._draw_hills(surface, far_offset, base_y=550, amplitude=90, wavelength=400, color=(160, 205, 185))

        # 4. Mid Hills (Medium parallax: 0.35)
        mid_offset = int(camera_x * 0.30) % SCREEN_WIDTH
        self._draw_hills(surface, mid_offset, base_y=600, amplitude=60, wavelength=280, color=(120, 185, 140))

    def _draw_hills(self, surface, offset, base_y, amplitude, wavelength, color):
        points = [(0, SCREEN_HEIGHT)]
        for x in range(0, SCREEN_WIDTH + 40, 40):
            world_x = x + offset
            y = base_y - math.sin(world_x / wavelength * 2 * math.pi) * amplitude
            points.append((x, int(y)))
        points.append((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.draw.polygon(surface, color, points)

    def draw_hud(self, surface, lives, stars, total_stars, level_num, gesture_name, pip_surface):
        """Draws in-game status, active gesture badge, and camera PiP."""
        # --- Top Left: Lives & Stars ---
        panel_rect = pygame.Rect(18, 16, 230, 84)
        panel_surf = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(panel_surf, COLOR_HUD_PANEL, (0, 0, panel_rect.width, panel_rect.height), border_radius=10)
        pygame.draw.rect(panel_surf, (100, 120, 160, 160), (0, 0, panel_rect.width, panel_rect.height), width=2, border_radius=10)
        surface.blit(panel_surf, panel_rect)

        # Level label
        lvl_text = self.font_small.render(f"LEVEL {level_num}", True, (200, 220, 255))
        surface.blit(lvl_text, (30, 24))

        # Hearts for Lives
        heart_x = 30
        for i in range(3):
            color = COLOR_BALL_BASE if i < lives else (90, 90, 100)
            self._draw_heart(surface, heart_x + i * 26, 52, color)

        # Stars collected
        star_icon_pts = self._get_star_polygon(138, 55, 10)
        pygame.draw.polygon(surface, COLOR_STAR, star_icon_pts)
        star_str = f"{stars} / {total_stars}"
        star_text = self.font_medium.render(star_str, True, COLOR_UI_TEXT)
        surface.blit(star_text, (156, 44))

        # --- Top Center: Gesture Pill ---
        badge_w, badge_h = 320, 44
        badge_x = (SCREEN_WIDTH - badge_w) // 2
        badge_y = 16
        pill_surf = pygame.Surface((badge_w, badge_h), pygame.SRCALPHA)
        
        # Color coding gesture badge
        pill_color = (25, 30, 45, 220)
        border_color = (80, 140, 240)
        if "ROLL" in gesture_name:
            border_color = (255, 170, 40)
        elif "JUMP" in gesture_name:
            border_color = (50, 240, 120)
        elif "BRAKE" in gesture_name:
            border_color = (240, 70, 70)

        pygame.draw.rect(pill_surf, pill_color, (0, 0, badge_w, badge_h), border_radius=22)
        pygame.draw.rect(pill_surf, border_color, (0, 0, badge_w, badge_h), width=2, border_radius=22)
        surface.blit(pill_surf, (badge_x, badge_y))

        # Gesture text
        g_render = self.font_medium.render(gesture_name, True, (255, 255, 255))
        g_rect = g_render.get_rect(center=(SCREEN_WIDTH // 2, badge_y + badge_h // 2))
        surface.blit(g_render, g_rect)

        # --- Top Right: Camera PiP ---
        if self.show_pip:
            pip_w, pip_h = 240, 180
            pip_x = SCREEN_WIDTH - pip_w - 18
            pip_y = 16

            if pip_surface is not None:
                scaled_cam = pygame.transform.smoothscale(pip_surface, (pip_w, pip_h))
                
                # Frame background / border
                pygame.draw.rect(surface, (15, 20, 30), (pip_x - 3, pip_y - 3, pip_w + 6, pip_h + 6), border_radius=8)
                surface.blit(scaled_cam, (pip_x, pip_y))
                pygame.draw.rect(surface, border_color, (pip_x - 2, pip_y - 2, pip_w + 4, pip_h + 4), width=2, border_radius=8)

                # Mini PiP header badge
                tag_surf = pygame.Surface((90, 18), pygame.SRCALPHA)
                pygame.draw.rect(tag_surf, (0, 0, 0, 180), (0, 0, 90, 18), border_radius=4)
                surface.blit(tag_surf, (pip_x + 6, pip_y + 6))
                tag_txt = self.font_small.render("LIVE HAND", True, (80, 240, 140))
                surface.blit(tag_txt, (pip_x + 12, pip_y + 7))
            else:
                # Informative fallback card when camera is not feeding frames
                panel_surf = pygame.Surface((pip_w, 90), pygame.SRCALPHA)
                pygame.draw.rect(panel_surf, (20, 25, 35, 220), (0, 0, pip_w, 90), border_radius=8)
                pygame.draw.rect(panel_surf, (100, 110, 130), (0, 0, pip_w, 90), width=2, border_radius=8)
                surface.blit(panel_surf, (pip_x, pip_y))
                
                txt1 = self.font_small.render("CAMERA OFFLINE", True, (240, 120, 120))
                txt2 = self.font_small.render("Keyboard Active (A/D/Space)", True, (200, 220, 240))
                txt3 = self.font_small.render("Press 'C' to hide", True, (140, 150, 170))
                surface.blit(txt1, (pip_x + 12, pip_y + 12))
                surface.blit(txt2, (pip_x + 12, pip_y + 36))
                surface.blit(txt3, (pip_x + 12, pip_y + 60))

    def _draw_heart(self, surface, x, y, color):
        """Draws small heart for lives HUD."""
        pts = [
            (x, y + 4),
            (x - 6, y - 4),
            (x - 4, y - 8),
            (x, y - 5),
            (x + 4, y - 8),
            (x + 6, y - 4)
        ]
        pygame.draw.polygon(surface, color, pts)

    def _get_star_polygon(self, cx, cy, r):
        pts = []
        for i in range(10):
            cur_r = r if i % 2 == 0 else r * 0.45
            a = i * math.pi / 5.0 - math.pi / 2.0
            pts.append((cx + math.cos(a) * cur_r, cy + math.sin(a) * cur_r))
        return pts

    def draw_start_screen(self, surface, pip_surface=None):
        """Renders interactive welcome screen with controls guide."""
        # Sky background
        self.draw_background(surface, 0)

        # Main Title Box
        title_text = self.font_title.render("RED BALL", True, (240, 45, 45))
        title_sub = self.font_large.render("HAND GESTURE ADVENTURE", True, (40, 50, 70))
        
        tx = SCREEN_WIDTH // 2 - title_text.get_width() // 2
        surface.blit(title_text, (tx, 90))
        surface.blit(title_sub, (SCREEN_WIDTH // 2 - title_sub.get_width() // 2, 150))

        # Instructions Panel
        box_w, box_h = 760, 310
        bx = (SCREEN_WIDTH - box_w) // 2
        by = 220
        box_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(box_surf, (20, 25, 35, 230), (0, 0, box_w, box_h), border_radius=16)
        pygame.draw.rect(box_surf, (80, 140, 230), (0, 0, box_w, box_h), width=2, border_radius=16)
        surface.blit(box_surf, (bx, by))

        # Instruction Items
        instructions = [
            ("Move Hand Left / Right", "Roll the Red Ball in that direction"),
            ("Point Index Finger Up / Upward Swipe", "Jump over pits and hazards"),
            ("Close Fist", "Brake & Stop quickly"),
            ("Keyboard Backup", "A / D or Arrows = Roll, Space / W = Jump")
        ]

        item_y = by + 25
        for header, detail in instructions:
            h_rend = self.font_medium.render(f">  {header}:", True, (255, 215, 60))
            d_rend = self.font_medium.render(detail, True, (220, 230, 245))
            surface.blit(h_rend, (bx + 35, item_y))
            surface.blit(d_rend, (bx + 35, item_y + 26))
            item_y += 65

        # Call to action flashing text
        t = pygame.time.get_ticks() / 350.0
        if int(t) % 2 == 0:
            prompt = self.font_large.render("Wave Hand or Press SPACE to Begin!", True, (30, 160, 60))
            surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 570))

        # Mini PiP in bottom-right corner
        pip_w, pip_h = 220, 165
        pip_x = SCREEN_WIDTH - pip_w - 24
        pip_y = SCREEN_HEIGHT - pip_h - 24
        if pip_surface is not None:
            scaled = pygame.transform.smoothscale(pip_surface, (pip_w, pip_h))
            pygame.draw.rect(surface, (15, 20, 30), (pip_x - 3, pip_y - 3, pip_w + 6, pip_h + 6), border_radius=8)
            surface.blit(scaled, (pip_x, pip_y))
            pygame.draw.rect(surface, (80, 220, 120), (pip_x - 2, pip_y - 2, pip_w + 4, pip_h + 4), width=2, border_radius=8)
            
            # Badge
            tag_surf = pygame.Surface((120, 20), pygame.SRCALPHA)
            pygame.draw.rect(tag_surf, (0, 0, 0, 190), (0, 0, 120, 20), border_radius=4)
            surface.blit(tag_surf, (pip_x + 6, pip_y + 6))
            tag_txt = self.font_small.render("WEBCAM READY", True, (80, 240, 140))
            surface.blit(tag_txt, (pip_x + 12, pip_y + 7))
        else:
            panel_surf = pygame.Surface((pip_w, 95), pygame.SRCALPHA)
            pygame.draw.rect(panel_surf, (20, 25, 35, 220), (0, 0, pip_w, 95), border_radius=8)
            pygame.draw.rect(panel_surf, (120, 130, 150), (0, 0, pip_w, 95), width=2, border_radius=8)
            surface.blit(panel_surf, (pip_x, pip_y + 70))
            txt1 = self.font_small.render("CAMERA STATUS: OFFLINE", True, (240, 120, 120))
            txt2 = self.font_small.render("Keyboard Mode Active", True, (255, 255, 255))
            txt3 = self.font_small.render("A/D to Roll, Space to Jump", True, (200, 220, 240))
            surface.blit(txt1, (pip_x + 10, pip_y + 80))
            surface.blit(txt2, (pip_x + 10, pip_y + 104))
            surface.blit(txt3, (pip_x + 10, pip_y + 126))

    def draw_level_clear(self, surface, level_num, stars, total_stars):
        """Displays level completion overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 25, 40, 210))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("LEVEL CLEARED!", True, (60, 235, 120))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 190))

        info = self.font_large.render(f"Stars Collected: {stars} / {total_stars}", True, COLOR_STAR)
        surface.blit(info, (SCREEN_WIDTH // 2 - info.get_width() // 2, 270))

        prompt = self.font_medium.render("Press SPACE or Point Up to Continue >>", True, (255, 255, 255))
        surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 380))

    def draw_game_over(self, surface):
        """Displays game over overlay."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((40, 10, 10, 220))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("GAME OVER", True, (245, 60, 60))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 220))

        prompt = self.font_large.render("Press 'R' or Raise Hand to Try Again", True, (255, 255, 255))
        surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 320))

    def draw_victory(self, surface):
        """Displays final all-levels victory screen."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((15, 35, 25, 225))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("CONGRATULATIONS!", True, (255, 215, 0))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 180))

        sub = self.font_large.render("You Conquered All Levels with Hand Gestures!", True, (220, 245, 220))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 260))

        prompt = self.font_medium.render("Press 'R' or SPACE to Play Again", True, (255, 255, 255))
        surface.blit(prompt, (SCREEN_WIDTH // 2 - prompt.get_width() // 2, 380))
