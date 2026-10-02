"""
Procedural sound effect synthesizer for Hand Gesture Red Ball Game.
Generates retro-arcade sound waves in memory without requiring external audio files.
"""

import numpy as np
import pygame
from config import SAMPLE_RATE, SOUND_VOLUME


class SoundManager:
    def __init__(self):
        self.enabled = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=2, buffer=512)
            self.enabled = True
        except Exception as e:
            print(f"[SoundManager] Warning: Audio mixer could not initialize: {e}")
            return

        self.sounds = {}
        if self.enabled:
            self._generate_all_sounds()

    def _make_sound(self, mono_samples):
        """Converts normalized float samples [-1.0, 1.0] to a Pygame Sound object."""
        # Clip to valid audio range
        clipped = np.clip(mono_samples, -1.0, 1.0)
        # Scale to 16-bit signed integer
        int16_samples = (clipped * 32767 * SOUND_VOLUME).astype(np.int16)
        # Duplicate to stereo
        stereo_samples = np.column_stack((int16_samples, int16_samples))
        return pygame.mixer.Sound(stereo_samples)

    def _generate_all_sounds(self):
        """Synthesizes jump, bounce, star pickup, damage, win, and game-over sounds."""
        # 1. Jump Sound (Ascending pitch sweep)
        dur = 0.16
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        freq = np.linspace(240, 680, n)
        env = np.linspace(1.0, 0.0, n) ** 1.5
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        jump_wave = (0.7 * np.sin(phase) + 0.3 * np.sign(np.sin(phase))) * env
        self.sounds["jump"] = self._make_sound(jump_wave)

        # 2. Bounce Spring Sound (High boing)
        dur = 0.28
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        freq = 200 + 700 * np.exp(-t * 8) + 120 * np.sin(2 * np.pi * 30 * t)
        env = np.exp(-t * 9)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        bounce_wave = np.sin(phase) * env
        self.sounds["bounce"] = self._make_sound(bounce_wave)

        # 3. Star Collect (Chime arpeggio: 880 Hz -> 1320 Hz -> 1760 Hz)
        notes = [880, 1320, 1760]
        note_dur = 0.07
        star_waves = []
        for f in notes:
            n_part = int(SAMPLE_RATE * note_dur)
            t_part = np.linspace(0, note_dur, n_part, endpoint=False)
            env_part = np.linspace(1.0, 0.1, n_part) ** 2
            wave_part = (np.sin(2 * np.pi * f * t_part) + 0.25 * np.sin(4 * np.pi * f * t_part)) * env_part
            star_waves.append(wave_part)
        star_wave = np.concatenate(star_waves)
        self.sounds["star"] = self._make_sound(star_wave)

        # 4. Spike / Damage Sound (Low discordant buzz)
        dur = 0.3
        n = int(SAMPLE_RATE * dur)
        t = np.linspace(0, dur, n, endpoint=False)
        freq = np.linspace(180, 60, n)
        noise = (np.random.rand(n) - 0.5) * 0.4
        env = np.linspace(1.0, 0.0, n)
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        spike_wave = (np.sign(np.sin(phase)) * 0.6 + noise) * env
        self.sounds["spike"] = self._make_sound(spike_wave)

        # 5. Victory Fanfare (Celebratory sequence)
        melody = [(523, 0.09), (659, 0.09), (784, 0.09), (1046, 0.25)]
        fanfare_parts = []
        for f, d in melody:
            n_part = int(SAMPLE_RATE * d)
            t_part = np.linspace(0, d, n_part, endpoint=False)
            env_part = np.linspace(1.0, 0.05, n_part)
            part = (0.6 * np.sin(2 * np.pi * f * t_part) + 0.4 * np.sin(4 * np.pi * f * t_part)) * env_part
            fanfare_parts.append(part)
        fanfare_wave = np.concatenate(fanfare_parts)
        self.sounds["win"] = self._make_sound(fanfare_wave)

        # 6. Checkpoint Sound
        cp_dur = 0.2
        n_cp = int(SAMPLE_RATE * cp_dur)
        t_cp = np.linspace(0, cp_dur, n_cp, endpoint=False)
        cp_wave = (np.sin(2 * np.pi * 587 * t_cp) + np.sin(2 * np.pi * 880 * t_cp)) * 0.5 * np.linspace(1.0, 0.0, n_cp)
        self.sounds["checkpoint"] = self._make_sound(cp_wave)

    def play(self, sound_name):
        """Plays sound effect if enabled."""
        if not self.enabled:
            return
        sound = self.sounds.get(sound_name)
        if sound:
            sound.play()
