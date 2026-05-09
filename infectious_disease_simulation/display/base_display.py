from abc import ABC, abstractmethod
import pygame

class BaseDisplay(ABC):
    """Abstract display surface; concrete impls are PygameDisplay and HeadlessDisplay."""
    def __init__(self, width: int, height: int, caption: str) -> None:
        self._width = width
        self._height = height
        self._caption = caption

    @abstractmethod
    def is_headless(self) -> bool: ...

    @abstractmethod
    def get_screen(self) -> pygame.Surface: ...

    @abstractmethod
    def update(self) -> None: ...

    @abstractmethod
    def fill(self, colour: tuple[int, int, int]) -> None: ...

    @abstractmethod
    def set_caption(self) -> None: ...

    @abstractmethod
    def set_display_icon(self, filepath: str) -> None: ...

    @abstractmethod
    def draw_text(self, text: str, pos: tuple[int, int] = (10, 10),
                  colour: tuple[int, int, int] = (0, 0, 0)) -> None: ...

    def get_width(self) -> int:
        return self._width

    def get_height(self) -> int:
        return self._height

    def get_caption(self) -> str:
        return self._caption