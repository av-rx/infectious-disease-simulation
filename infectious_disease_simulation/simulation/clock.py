"""
Simulation clock: paces the simulation, drives population/graph updates, draws the time HUD.
"""

from ..display import Display # For typing
from ..simulation import population # For typing
from ..simulation.pacer import Pacer
from ..viz import plot_graph

class Clock:
    """Tracks simulated day/hour, drives infection updates, and triggers commute movement."""
    def __init__(self, display_obj: Display,
                 population_obj: population.Population,
                 pacer: Pacer,
                 fps: int) -> None:
        """
        Args:
            display_obj: Display surface (real or headless).
            population_obj: The population to update each simulated hour.
            pacer: Strategy that decides when the simulated hour should tick over.
            fps: Display frames per second.
        """
        self.__day: int = 1
        self.__hour: int = 0
        self.__running: bool = True
        self.__pacer: Pacer = pacer
        self.__fps: int = fps
        self.__display: Display = display_obj
        self.__population: population.Population = population_obj
        if not self.__display.is_headless():
            self.__graph: plot_graph.PlotGraph = plot_graph.PlotGraph(self.__display.get_caption(), self.__fps)
            self.__graph.update(self.__day, self.__hour, self.__population.get_status_counts())

    def update_time(self) -> None:
        """Advance the simulation clock and update the population once per simulated hour."""
        if not self.__running:
            return

        # No infections left - flush a final update and stop
        if not self.__population.has_active_infections():
            self.__population.update_infection_status()
            counts = self.__population.get_status_counts()
            if not self.__display.is_headless():
                self.__graph.update(self.__day, self.__hour, counts)
            self.__running = False
            return

        if not self.__pacer.should_advance_hour():
            return

        self.__hour += 1
        self.__population.update_infection_status()

        counts = self.__population.get_status_counts()
        if not self.__display.is_headless():
            self.__graph.update(self.__day, self.__hour, counts)

        if self.__hour > 24:
            self.__hour = 1
            self.__day += 1

        # People reach office by 9, leave at 17
        for individual in self.__population.get_people():
            if self.__hour == individual.get_leave_home():
                individual.start_move_to_office()
            elif self.__hour == 17:
                individual.start_move_to_home()

    def display_time(self) -> None:
        """Draw the current simulated time on the display."""
        time_text = f"Day: {self.__day}, Hour: {self.__hour}" if self.__running else "Simulation Ended"
        self.__display.draw_text(time_text, pos=(10, 10), colour=(0, 0, 0))

    def get_running(self) -> bool:
        return self.__running

    def get_day(self) -> int:
        return self.__day

    def get_hour(self) -> int:
        return self.__hour
