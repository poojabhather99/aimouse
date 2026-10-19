"""OS integration: mouse, scrolling and (on Windows) master volume."""
from __future__ import annotations

import sys

import pyautogui


class MouseController:
    def __init__(self) -> None:
        pyautogui.FAILSAFE = True  # slam the cursor into a screen corner to abort
        pyautogui.PAUSE = 0
        self.screen = tuple(pyautogui.size())

    def move(self, x: float, y: float) -> None:
        pyautogui.moveTo(x, y, _pause=False)

    def click(self) -> None:
        pyautogui.click()

    def scroll(self, amount: int) -> None:
        pyautogui.scroll(amount)


class VolumeController:
    """Windows-only master volume via pycaw. Becomes a no-op elsewhere."""

    def __init__(self) -> None:
        self.available = False
        if not sys.platform.startswith("win"):
            return
        try:
            from ctypes import POINTER, cast

            from comtypes import CLSCTX_ALL
            from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

            speakers = AudioUtilities.GetSpeakers()
            interface = speakers.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            self._endpoint = cast(interface, POINTER(IAudioEndpointVolume))
            self._min, self._max = self._endpoint.GetVolumeRange()[:2]
            self.available = True
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - platform specific
            print(f"Volume control disabled: {exc}")

    def set_percent(self, percent: float) -> None:
        if self.available:
            level = self._min + (self._max - self._min) * percent / 100.0
            self._endpoint.SetMasterVolumeLevel(level, None)
