"""
sound_manager.py
Generates all game sounds procedurally using numpy + pygame.
No external audio files needed.
"""

import numpy as np
import pygame

pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()

SAMPLE_RATE = 44100


def _make_sound(samples: np.ndarray) -> pygame.mixer.Sound:
    """Convert a float32 numpy array (-1..1) to a stereo pygame Sound."""
    data = np.clip(samples, -1, 1)
    data = (data * 32767).astype(np.int16)
    # Stereo: duplicate mono channel into 2 columns
    stereo = np.column_stack((data, data))
    return pygame.sndarray.make_sound(stereo)


def _sine(freq, duration, sr=SAMPLE_RATE):
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)
    return np.sin(2 * np.pi * freq * t)


def _envelope(samples, attack=0.01, decay=0.1, sr=SAMPLE_RATE):
    n = len(samples)
    env = np.ones(n)
    a = int(attack * sr)
    d = int(decay * sr)
    if a > 0:
        env[:a] = np.linspace(0, 1, a)
    if d > 0 and d < n:
        env[n - d:] = np.linspace(1, 0, d)
    return samples * env


# ── SLICE  — short swoosh + high tick ──
def _build_slice():
    dur = 0.18
    t = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    freq = np.linspace(900, 300, len(t))
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    tick = _sine(1800, 0.03) * 0.6
    wave[:len(tick)] += tick
    wave = _envelope(wave, attack=0.005, decay=0.06) * 0.7
    return _make_sound(wave)


# ── COMBO  — rising arpeggio ──
def _build_combo():
    notes = [523, 659, 784, 1047]
    seg   = 0.07
    parts = []
    for f in notes:
        s = _sine(f, seg) * 0.5
        s = _envelope(s, attack=0.005, decay=0.04)
        parts.append(s)
    wave = np.concatenate(parts)
    return _make_sound(wave)


# ── BOMB  — low thud + rumble ──
def _build_bomb():
    dur = 0.55
    t   = np.linspace(0, dur, int(SAMPLE_RATE * dur))
    freq = np.linspace(120, 30, len(t))
    wave = np.sin(2 * np.pi * np.cumsum(freq) / SAMPLE_RATE)
    noise = np.random.uniform(-1, 1, len(t)) * np.exp(-t * 8)
    wave  = wave * np.exp(-t * 4) + noise * 0.5
    wave  = _envelope(wave, attack=0.005, decay=0.15) * 0.85
    return _make_sound(wave)


# ── HIGH SCORE  — fanfare ──
def _build_highscore():
    melody = [523, 659, 784, 659, 1047]
    durs   = [0.1, 0.1, 0.1, 0.08, 0.28]
    parts  = []
    for f, d in zip(melody, durs):
        s = _sine(f, d) * 0.55
        s += _sine(f * 1.5, d) * 0.2
        s = _envelope(s, attack=0.01, decay=0.05)
        parts.append(s)
    wave = np.concatenate(parts)
    return _make_sound(wave)


# ── MENU TICK  — soft click ──
def _build_tick():
    wave = _sine(440, 0.06) * 0.4
    wave = _envelope(wave, attack=0.003, decay=0.03)
    return _make_sound(wave)


class SoundManager:
    def __init__(self):
        self.enabled    = True
        self._slice     = _build_slice()
        self._combo     = _build_combo()
        self._bomb      = _build_bomb()
        self._highscore = _build_highscore()
        self._tick      = _build_tick()

        self._slice    .set_volume(0.7)
        self._combo    .set_volume(0.85)
        self._bomb     .set_volume(0.9)
        self._highscore.set_volume(0.8)
        self._tick     .set_volume(0.5)

    def _play(self, sound):
        if self.enabled:
            sound.play()

    def play_slice(self):     self._play(self._slice)
    def play_combo(self):     self._play(self._combo)
    def play_bomb(self):      self._play(self._bomb)
    def play_highscore(self): self._play(self._highscore)
    def play_tick(self):      self._play(self._tick)