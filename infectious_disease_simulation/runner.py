"""SimulationRunner: wires together map, disease, population, clock, and runs the main loop."""

import pygame

from .config import Config
from .display.base_display import BaseDisplay
from .simulation import clock, disease, population
from .world import create_map


class SimulationRunner:
    """Owns every simulation subsystem and drives the per-frame loop."""

    def __init__(self, config: Config, display: BaseDisplay) -> None:
        self.__config = config
        self.__display = display
        self.__seconds_per_hour: float = 1 / config.simulation_speed
        self.__fps: int = 60

        self.__initialise_display()

        # The map renders into the screen surface; copy that to a separate surface
        # so we can blit it as a static background each frame instead of redrawing.
        self.__map_surface = pygame.Surface((display.get_width(), display.get_height()))
        self.__map = create_map.CreateMap(display,
                                          config.num_houses, config.num_offices,
                                          config.building_size, config.building_size)
        self.__map.draw(config.show_drawing, config.additional_roads)
        self.__map_surface.blit(display.get_screen(), (0, 0))

        self.__disease = disease.Disease(config.infection_rate,
                                         config.incubation_time,
                                         config.recovery_rate,
                                         config.mortality_rate,
                                         self.__seconds_per_hour)

        print("Initialising Population...")
        self.__population = population.Population(config.num_people_in_house,
                                                  display, self.__map, self.__disease,
                                                  self.__seconds_per_hour, self.__fps)

        self.__clock = clock.Clock(display, self.__population,
                                   self.__seconds_per_hour, self.__fps)

    def __initialise_display(self) -> None:
        """Set caption, clear to white, set window icon."""
        self.__display.set_caption()
        self.__display.fill((255, 255, 255))
        self.__display.set_display_icon("images\\virus_icon.png")

    def run(self) -> None:
        """Main loop: advance time, move people, render. Exits on window close (or end of sim in headless)."""
        print("Running Simulation...")
        running = True
        pygame_clock = pygame.time.Clock()

        while running:
            if not self.__display.is_headless():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

            if self.__clock.get_running():
                self.__clock.update_time()
                self.__population.update_positions()
                self.__display.get_screen().blit(self.__map_surface, (0, 0))
                self.__population.draw_people()
            elif self.__display.is_headless():
                # Nothing left to simulate and no window to keep open
                running = False

            self.__clock.display_time()
            self.__display.update()
            pygame_clock.tick(self.__fps)

        pygame.quit()
