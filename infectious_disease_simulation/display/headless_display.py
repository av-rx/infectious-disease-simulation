import pygame
from .base_display import BaseDisplay

class HeadlessDisplay(BaseDisplay):
    """Null display: matches BaseDisplay's interface but renders nothing."""

    def __init__(self, width: int, height: int, caption: str) -> None:
        super().__init__(width, height, caption)
        # Dummy surface so existing pygame.draw.* calls in Tilemap/Roads/Person are harmless no-ops
        self.__screen = pygame.Surface((width, height))

    def is_headless(self) -> bool:
        return True

    def set_caption(self) -> None:
        pass

    def fill(self, colour: tuple[int, int, int]) -> None:
        pass

    def update(self) -> None:
        pass

    def get_screen(self) -> pygame.Surface:
        return self.__screen

    def set_display_icon(self, filepath: str) -> None:
        pass

    def draw_text(self, text: str, pos: tuple[int, int] = (10, 10),
                  colour: tuple[int, int, int] = (0, 0, 0)) -> None:
        pass
