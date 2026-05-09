"""SimulationRunner: wires together map, disease, population, clock, and runs the main loop."""

import random

import pygame

from .config import Config
from .display.base_display import BaseDisplay
from .paths import asset_path
from .simulation import clock, disease, population
from .simulation.pacer import Pacer, RealTimePacer, TickPacer
from .world import create_map


class SimulationRunner:
    """Owns every simulation subsystem and drives the per-frame loop."""

    def __init__(self, config: Config, display: BaseDisplay,
                 rng: random.Random | None = None,
                 seed: int | None = None) -> None:
        """
        Args:
            config: Validated simulation parameters.
            display: Display surface (pygame or headless).
            rng: Optional RNG threaded through the whole subsystem stack.
                 Pass a seeded random.Random for reproducible runs.
            seed: The seed used to build `rng`, kept around purely for the headless
                  end-of-run summary print. Has no effect on the simulation itself.
        """
        self.__config = config
        self.__display = display
        self.__rng: random.Random = rng or random.Random()
        self.__seed = seed
        self.__seconds_per_hour: float = 1 / config.simulation_speed
        self.__fps: int = 60

        self.__initialise_display()

        # The map renders into the screen surface; copy that to a separate surface
        # so we can blit it as a static background each frame instead of redrawing.
        self.__map_surface = pygame.Surface((display.get_width(), display.get_height()))
        self.__map = create_map.CreateMap(display,
                                          config.num_houses, config.num_offices,
                                          config.building_size, config.building_size,
                                          rng=self.__rng)
        self.__map.draw(config.show_drawing, config.additional_roads)
        self.__map_surface.blit(display.get_screen(), (0, 0))

        self.__disease = disease.Disease(config.infection_rate,
                                         config.incubation_time,
                                         config.recovery_rate,
                                         config.mortality_rate,
                                         self.__seconds_per_hour,
                                         rng=self.__rng)

        print("Initialising Population...")
        self.__population = population.Population(config.num_people_in_house,
                                                  display, self.__map, self.__disease,
                                                  self.__seconds_per_hour, self.__fps,
                                                  rng=self.__rng)

        pacer = self.__build_pacer()
        self.__clock = clock.Clock(display, self.__population, pacer, self.__fps)

    def __build_pacer(self) -> Pacer:
        """Real-time pacing for the GUI; tick-based pacing for headless to run unthrottled."""
        if self.__display.is_headless():
            # Same frames-per-hour ratio the original real-time loop produced, just decoupled
            # from the wall clock so it can run as fast as Python iterates.
            return TickPacer(frames_per_hour=self.__fps * self.__seconds_per_hour)
        return RealTimePacer(self.__seconds_per_hour)

    def __initialise_display(self) -> None:
        """Set caption, clear to white, set window icon."""
        self.__display.set_caption()
        self.__display.fill((255, 255, 255))
        self.__display.set_display_icon(str(asset_path("virus_icon.png")))

    def run(self) -> None:
        """Main loop: advance time, move people, render. Exits on window close (or end of sim in headless)."""
        print("Running Simulation...")
        running = True
        pygame_clock = pygame.time.Clock()
        headless = self.__display.is_headless()

        while running:
            if not headless:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False

            if self.__clock.get_running():
                self.__clock.update_time()
                self.__population.update_positions()
                self.__display.get_screen().blit(self.__map_surface, (0, 0))
                self.__population.draw_people()
            elif headless:
                # Nothing left to simulate and no window to keep open
                running = False

            self.__clock.display_time()
            self.__display.update()

            # Only throttle to 60 fps when there's a UI to feed; headless runs flat-out
            if not headless:
                pygame_clock.tick(self.__fps)

        pygame.quit()

        if headless:
            self.__report_final_state()

    def __report_final_state(self) -> None:
        """Print the simulated end time, final S/E/I/R/D counts, and seed (headless only)."""
        counts = self.__population.get_status_counts()
        seed_str = f"seed={self.__seed}" if self.__seed is not None else "no seed"
        print(f"Simulation ended at Day {self.__clock.get_day()}, Hour {self.__clock.get_hour()} ({seed_str})")
        print(f"Final counts: S={counts['S']}, E={counts['E']}, "
              f"I={counts['I']}, R={counts['R']}, D={counts['D']}")
