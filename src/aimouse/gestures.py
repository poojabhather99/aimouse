"""Pure gesture logic: no camera, no OS calls, fully unit-testable.

Landmarks are the 21 MediaPipe hand points as ``[id, x_px, y_px]`` rows.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

THUMB_TIP, INDEX_TIP, MIDDLE_TIP = 4, 8, 12
TIP_IDS = (4, 8, 12, 16, 20)

Landmarks = list[list[int]]


@dataclass(frozen=True)
class Config:
    cam_width: int = 1280
    cam_height: int = 720
    frame_margin: int = 5          # dead border inside the camera frame, in px
    smoothing: float = 7.0         # higher = smoother but laggier cursor
    click_distance: float = 40.0   # px between index and middle tips that counts as a click
    volume_min_px: float = 50.0    # pinch distance mapped to minimum volume
    volume_max_px: float = 200.0   # pinch distance mapped to maximum volume
    scroll_amount: int = 300


def fingers_up(lm: Landmarks) -> list[int]:
    """Return [thumb, index, middle, ring, pinky], 1 if raised."""
    state = [1 if lm[TIP_IDS[0]][1] > lm[TIP_IDS[0] - 1][1] else 0]
    for i in range(1, 5):
        state.append(1 if lm[TIP_IDS[i]][2] < lm[TIP_IDS[i] - 2][2] else 0)
    return state


def distance(lm: Landmarks, a: int, b: int) -> float:
    return math.hypot(lm[a][1] - lm[b][1], lm[a][2] - lm[b][2])


def camera_to_screen(x: float, y: float, cfg: Config, screen: tuple[int, int]) -> tuple[float, float]:
    """Map a point inside the camera frame (minus margin) to screen coordinates."""
    sx = np.interp(x, (cfg.frame_margin, cfg.cam_width - cfg.frame_margin), (0, screen[0]))
    sy = np.interp(y, (cfg.frame_margin, cfg.cam_height - cfg.frame_margin), (0, screen[1]))
    return float(sx), float(sy)


def smooth(prev: tuple[float, float], target: tuple[float, float], factor: float) -> tuple[float, float]:
    """Exponential smoothing step toward ``target``."""
    return (prev[0] + (target[0] - prev[0]) / factor, prev[1] + (target[1] - prev[1]) / factor)


def pinch_to_volume_percent(length_px: float, cfg: Config) -> float:
    """Map thumb-index pinch distance to a 0-100 volume percentage."""
    return float(np.interp(length_px, (cfg.volume_min_px, cfg.volume_max_px), (0, 100)))


def classify(fingers: list[int]) -> str:
    """Name the active mode for a finger state."""
    thumb, index, middle, _ring, pinky = fingers
    if index and middle:
        return "click"
    if index and not middle:
        return "move_pinch_volume" if thumb else "move"
    if thumb:
        return "scroll_up"
    if pinky:
        return "scroll_down"
    return "idle"
