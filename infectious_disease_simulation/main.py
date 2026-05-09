"""
Entry point: parse args, get a Config (GUI or headless file), wire up the simulation, run.

Note: this file will be split into cli/paths/config_sources/runner in stage 2 of the refactor.
"""

import pygame
import os
import sys
import json
from .ui.interface import Interface
from .display import Display
from .world import create_map
from .simulation import disease
from .simulation import population
from .simulation import clock
from .config import Config
from .errors import ConfigError, DBError, UsageError
from .storage.db_handler import DBHandler

class Main:
    """Bootstraps and runs a single simulation."""
    def __init__(self) -> None:
        args = sys.argv[1:]
        self.__headless = "--headless" in args
        if self.__headless:
            args.remove("--headless")

        # If in headless mode, next argument must be config file path
        config_path: str | None = None
        if self.__headless:
            try:
                if len(args) == 0:
                    raise UsageError("\n--headless flag used but no config file provided.\nFlag usage: --headless <config_file_path>")
                elif len(args) > 1:
                    raise UsageError("\nToo many arguments provided.\nFlag usage: --headless <config_file_path>")
            except UsageError as e:
                print(e)
                return
            config_path = args[0]

        # Pulls database name
        db_name: str = self.__get_db_name()

        if self.__headless:
            self.__config = self.__load_config_file(config_path)
        else:
            # Initialise interface and get parameters
            ui = Interface(db_name)
            self.__config = ui.get_config()

            if self.__config is None:
                return  # User closed the window


        # Initialise class to handle SQL queries
        try:
            with DBHandler(db_name) as db_handler:
                db_handler.save_params(self.__config)
            print("Parameters saved successfully.")
        except DBError as e:
            print(f"Error while saving parameters: {e}")

        # Configure timescales
        self.__seconds_per_hour: float = 1 / self.__config.simulation_speed
        self.__fps: int = 60

        # Initialise display with parameters
        self.__display: Display = Display(self.__config.display_size,
                                          self.__config.display_size,
                                          self.__config.simulation_name,
                                          self.__headless)
        self.__initialise_display()

        # Create a separate surface for the map, intialise and draw map with parameters
        self.__map_surface: pygame.Surface = pygame.Surface((self.__display.get_width(), self.__display.get_height()))
        self.__map: create_map.CreateMap = create_map.CreateMap(self.__display,
                                                               self.__config.num_houses,
                                                               self.__config.num_offices,
                                                               self.__config.building_size,
                                                               self.__config.building_size)
        self.__map.draw(self.__config.show_drawing, self.__config.additional_roads)

        # Draw map onto map surface
        self.__map_surface.blit(self.__display.get_screen(), (0, 0))

        # Initialise disease with parameters
        self.__disease: disease.Disease = disease.Disease(self.__config.infection_rate,
                                                          self.__config.incubation_time,
                                                          self.__config.recovery_rate,
                                                          self.__config.mortality_rate,
                                                          self.__seconds_per_hour)

        # Initialise population with parameters
        print("Initialising Population...")
        self.__population: population.Population = population.Population(self.__config.num_people_in_house,
                                                                         self.__display,
                                                                         self.__map,
                                                                         self.__disease,
                                                                         self.__seconds_per_hour,
                                                                         self.__fps)

        # Initialise clock with parameters
        self.__clock: clock.Clock = clock.Clock(self.__display, self.__population, self.__seconds_per_hour, self.__fps)

        # Run simulation
        print("Running Simulation...")
        self.__run_simulation()

    def __load_config_file(self, path: str) -> Config:
        """Load and validate a headless config from a JSON file."""
        try:
            with open(path) as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"Configuration file not found at: {path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"Configuration file is not valid JSON: {e}")
            sys.exit(1)

        try:
            return Config.from_dict(data)
        except ConfigError as e:
            print(f"Invalid configuration: {e}")
            sys.exit(1)

    def __initialise_display(self) -> None:
        """Set caption, clear to white, set window icon."""
        self.__display.set_caption()
        self.__display.fill((255, 255, 255))
        self.__display.set_display_icon("images\\virus_icon.png")

    def __run_simulation(self) -> None:
        """Main loop: update time, move people, render. Exits on window close (or natural end in headless mode)."""
        running: bool = True # Flag for running
        pygame_clock: pygame.time.Clock = pygame.time.Clock()

        # Enter simulation loop
        while running:
            if not self.__display.is_headless():
                for event in pygame.event.get():
                    if event.type == pygame.QUIT: # Handle quitting
                        running = False

            if self.__clock.get_running():
                self.__clock.update_time() # Update simulation time
                self.__population.update_positions() # Update people's positions
                self.__display.get_screen().blit(self.__map_surface, (0, 0)) # Map surface as 'background'
                self.__population.draw_people() # Draw people
            else:
                if self.__headless:
                    running = False
            
            self.__clock.display_time() # Draw the clock on top
            self.__display.update()
            pygame_clock.tick(self.__fps) # Update required parts every frame
        pygame.quit()

    def __get_db_name(self, db_name: str = "simulation_params.db") -> str:
        """Resolve the database path under $XDG_DATA_HOME (or ~/.local/share), falling back to cwd on failure."""
        # Logic adapted from pyxdg: https://cgit.freedesktop.org/xdg/pyxdg/tree/xdg/BaseDirectory.py
        _home = os.path.expanduser('~')
        xdg_data_home = os.environ.get('XDG_DATA_HOME') or os.path.join(_home, '.local', 'share')
        dir_path = os.path.join(xdg_data_home, "infectious-disease-simulation")

        try:
            os.makedirs(dir_path, exist_ok=True)
        except OSError as err:
            print(f"Could not create data dir, using current directory: {err}")
            dir_path = os.path.curdir

        return os.path.join(dir_path, db_name)

# Run the main program
if __name__ == "__main__":
    Main()
