"""
Pygame-backed display: real window, real rendering.
"""

import pygame
from .base_display import BaseDisplay

class PygameDisplay(BaseDisplay):
    """Owns the pygame window, screen surface, and font used for the on-screen clock."""

    def __init__(self, width: int, height: int, caption: str) -> None:
        super().__init__(width, height, caption)
        self.__screen: pygame.Surface = pygame.display.set_mode((self._width, self._height))
        pygame.font.init()
        self.__font: pygame.font.Font = pygame.font.SysFont('Arial Bold', 25)

    def is_headless(self) -> bool:
        return False

    def set_caption(self) -> None:
        pygame.display.set_caption(self._caption)

    def fill(self, colour: tuple[int, int, int]) -> None:
        self.__screen.fill(colour)

    def update(self) -> None:
        pygame.display.update()

    def set_display_icon(self, filepath: str) -> None:
        """Set the window icon. Silently ignored if the file is missing or invalid."""
        try:
            icon: pygame.Surface = pygame.image.load(filepath)
            pygame.display.set_icon(icon)
        except (FileNotFoundError, pygame.error):
            pass

    def get_screen(self) -> pygame.Surface:
        return self.__screen

    def draw_text(self, text: str, pos: tuple[int, int] = (10, 10),
                  colour: tuple[int, int, int] = (0, 0, 0)) -> None:
        surface = self.__font.render(text, True, colour)
        self.__screen.blit(surface, pos)
