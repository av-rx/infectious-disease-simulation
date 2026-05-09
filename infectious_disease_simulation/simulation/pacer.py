"""Pacers control when the simulated clock advances by an hour.

Two strategies:
- RealTimePacer: gates advancement on wall-clock seconds (used for the GUI so the user
  can actually watch the simulation play out).
- TickPacer: advances every N frames, ignoring wall-clock entirely. Used in headless
  mode so runs go as fast as Python can iterate.
"""

import time
from abc import ABC, abstractmethod


class Pacer(ABC):
    """Decides, on each update_time call, whether the simulated clock should tick by one hour."""

    @abstractmethod
    def should_advance_hour(self) -> bool: ...


class RealTimePacer(Pacer):
    """Advances once `seconds_per_hour` real seconds have elapsed since the last tick."""

    def __init__(self, seconds_per_hour: float) -> None:
        self.__seconds_per_hour = seconds_per_hour
        self.__last_tick = time.time()

    def should_advance_hour(self) -> bool:
        now = time.time()
        if now - self.__last_tick >= self.__seconds_per_hour:
            self.__last_tick = now
            return True
        return False


class TickPacer(Pacer):
    """Advances after a fixed number of update_time calls.

    Preserves the original frame-to-hour ratio (`fps * seconds_per_hour` frames per
    simulated hour) so people still get the right number of position updates per hour.
    Fractional frame counts are tracked as floats so we don't accumulate drift.
    """

    def __init__(self, frames_per_hour: float) -> None:
        self.__threshold = frames_per_hour
        self.__count = 0.0

    def should_advance_hour(self) -> bool:
        self.__count += 1
        if self.__count >= self.__threshold:
            # Subtract (rather than reset to 0) to preserve any fractional remainder
            self.__count -= self.__threshold
            return True
        return False
