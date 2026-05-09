"""
Person: a single agent's state, movement along their commute, and disease progression.
"""
import math
import pygame
from ..display import Display # For typing
from ..simulation import disease # For typing

class Person:
    """One agent: position, commute routes, and SEIRD status."""
    def __init__(self, display_obj: Display,
                 person_id: int,
                 home_location: tuple[int, int], office_location: tuple[int, int], home_position: tuple[int, int],
                 home_radius: int, office_radius: int,
                 home_to_office_route: list[tuple[int, int]],
                 speed: float, leave_home: int, status: str,
                 disease_obj: disease.Disease, incubation_time: float,
                 seconds_per_hour: float, delta_time: float) -> None:
        self.__display: Display = display_obj
        self.__person_id: int = person_id
        self.__home_location: tuple[int, int] = home_location
        self.__office_location: tuple[int, int] = office_location
        self.__current_location: tuple[int, int] = self.__home_location
        self.__home_position: tuple[int, int] = home_position
        self.__office_position: tuple[int, int] | None = None
        self.__current_position: tuple[int, int] = self.__home_position
        self.__home_radius: int = home_radius
        self.__office_radius: int = office_radius
        self.__home_to_office_route: list[tuple[int, int]] = home_to_office_route
        self.__office_to_home_route: list[tuple[int, int]] | None = None
        self.__speed: float = speed
        self.__leave_home: int = leave_home
        self.__status: str = status  # S = Susceptible, E = Exposed, I = Infected, R = Recovered, D = Deceased
        self.__route: list[tuple[int, int]] | None = None
        self.__route_index: int = 0
        self.__moving: bool = False
        self.__disease: disease.Disease = disease_obj
        self.__incubation_time: float = incubation_time
        self.__seconds_per_hour: float = seconds_per_hour
        self.__delta_time: float = delta_time

    def draw_person(self) -> None:
        """Draw the person as a coloured circle at their current position."""
        pygame.draw.circle(self.__display.get_screen(),
                           self.get_colour(),
                           (int(self.__current_position[0]), int(self.__current_position[1])),
                           self.get_radius())

    def get_leave_home(self) -> int:
        return self.__leave_home

    def get_home_location(self) -> tuple[int, int]:
        return self.__home_location

    def get_office_location(self) -> tuple[int, int]:
        return self.__office_location

    def get_current_location(self) -> tuple[int, int]:
        return self.__current_location

    def set_current_location(self, new_location: tuple[int, int]) -> None:
        self.__current_location = new_location

    def get_home_position(self) -> tuple[int, int]:
        return self.__home_position

    def get_office_position(self) -> tuple[int, int] | None:
        return self.__office_position

    def set_office_position(self, office_position: tuple[int, int]) -> None:
        """Set the office pixel position and finalise both commute routes around it."""
        # Routes from Dijkstra are tile-centred; bookend with exact home/office positions
        self.__office_position = office_position
        self.__home_to_office_route.insert(0, self.__home_position)
        self.__home_to_office_route.append(office_position)
        self.__office_to_home_route = list(reversed(self.__home_to_office_route))

    def get_current_position(self) -> tuple[int, int]:
        return self.__current_position

    def set_current_position(self, new_position: tuple[int, int]) -> None:
        self.__current_position = new_position

    def get_radius(self) -> int:
        """Drawing radius depends on whether the person is at home or at their office."""
        if self.__current_position == self.__home_position:
            return self.__home_radius
        return self.__office_radius

    def get_colour(self) -> tuple[int, int, int]:
        """RGB colour for this person's SEIRD status."""
        status_colours = {
            "S": (144, 238, 144),  # Green
            "E": (255, 255, 0),    # Yellow
            "I": (255, 0, 0),      # Red
            "R": (204, 153, 255),  # Light Purple
            "D": (50, 50, 50)      # Dark Grey
        }
        return status_colours[self.__status]

    def start_move_to_office(self) -> None:
        if self.__status != 'D':
            self.__route = self.__home_to_office_route
            self.__route_index = 0
            self.__moving = True

    def start_move_to_home(self) -> None:
        if self.__status != 'D':
            self.__route = self.__office_to_home_route
            self.__route_index = 0
            self.__moving = True

    def update_position(self) -> None:
        """Step along the active route by `speed`; snap to next waypoint when within one step."""
        if self.__status == 'D':
            self.__moving = False
            self.draw_person()
            return

        if self.__moving and self.__route is not None and self.__route_index < len(self.__route):
            next_position: tuple[int, int] = self.__route[self.__route_index]
            dx: float = next_position[0] - self.__current_position[0]
            dy: float = next_position[1] - self.__current_position[1]
            distance: float = math.sqrt(dx ** 2 + dy ** 2)
            if distance < self.__speed:
                # Snap to waypoint to avoid overshoot, advance index
                self.__current_position = next_position
                self.__route_index += 1
                if self.__route_index >= len(self.__route):
                    self.__moving = False
            else:
                dx = dx / distance * self.__speed
                dy = dy / distance * self.__speed
                self.__current_position = (self.__current_position[0] + dx, self.__current_position[1] + dy)

    def update_infection_status(self) -> None:
        """Advance disease state: E counts down incubation, I rolls for recovery then death."""
        if self.__status == "E":
            self.__incubation_time -= self.__seconds_per_hour
            if self.__incubation_time <= 0:
                self.__status = "I"
        elif self.__status == "I":
            if self.__disease.recover(self.__delta_time):
                self.__status = "R"
            elif self.__disease.die(self.__delta_time):
                self.__status = "D"
                self.__moving = False

    def get_status(self) -> str:
        return self.__status

    def set_status(self, status: str) -> None:
        self.__status = status

    def get_person_id(self) -> int:
        return self.__person_id

    def get_home_to_office_route(self) -> list[tuple[int, int]]:
        return self.__home_to_office_route
