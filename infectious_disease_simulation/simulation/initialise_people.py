"""
Builds the initial population: assigns homes, offices, routes, speeds, and one starting infection.
"""

import random
import math
from ..display import Display # For typing
from ..world import tilemap # For typing
from ..world import create_map # For typing
from ..simulation import disease # For typing
from ..agents import person
from ..agents import dijkstra

class InitialisePeople:
    """One-shot population builder. Call `.get_people()` once after construction."""
    def __init__(self, num_in_house: int,
                 display_obj: Display, map_obj: create_map.CreateMap, disease_obj: disease.Disease,
                 seconds_per_hour: float, fps: int) -> None:
        self.__display: Display = display_obj
        self.__map: create_map.CreateMap = map_obj
        self.__tilemap: tilemap.Tilemap = self.__map.get_tilemap()
        self.__disease: disease.Disease = disease_obj
        self.__num_in_house: int = num_in_house
        self.__seconds_per_hour: float = seconds_per_hour
        self.__fps: int = fps
        self.__delta_time: float = 1 / self.__fps
        self.__roads: dict[tuple[int, int], list[tuple[tuple[int, int], int]]] = self.__map.get_roads()
        self.__building_width: int = self.__tilemap.get_building_width()
        self.__building_height: int = self.__tilemap.get_building_height()
        self.__dijkstra: dijkstra.Dijkstra = dijkstra.Dijkstra(self.__roads)
        self.__people: list[person.Person] = self.__initialise_people()

    def get_people(self) -> list[person.Person]:
        return self.__people

    def __initialise_people(self) -> list[person.Person]:
        """Build every Person, place them in homes/offices, and seed one initial infection."""
        people: list[person.Person] = [] # Initialise list

        # Get required values
        num_people: int = self.__tilemap.get_num_houses() * self.__num_in_house
        infected_person_id: int = random.randint(0, num_people - 1)
        office_location_dist: list[tuple[int, int]] = self.__calculate_office_location_dist(num_people)
        random.shuffle(office_location_dist)
        office_location_dist_dict: dict[tuple[int, int], int] = self.__convert_list_to_dict(office_location_dist)

        # Calculate and set values for each person's parameters
        for person_id in range(num_people):
            home_location: tuple[int, int] = self.__calculate_home_location(person_id, self.__num_in_house)
            office_location: tuple[int, int] = self.__calculate_office_location(person_id, office_location_dist)
            home_position: tuple[int, int] = self.__calculate_home_position(person_id, self.__num_in_house, home_location)
            home_radius: int = self.__calculate_radius(self.__num_in_house)
            office_radius: int = self.__calculate_radius(office_location_dist_dict[office_location])
            home_to_office_route, route_weight = self.__dijkstra.compute(home_location, office_location)
            home_to_office_route: list[tuple[int, int]] = self.__scale_xy_list(home_to_office_route)
            speed: float = self.__calculate_speed()
            time_to_travel: float = self.__calculate_time_to_travel((route_weight + 0.5), speed)
            leave_home: int = self.__calculate_leave_home(time_to_travel)
            status: str = self.__calculate_status(person_id, infected_person_id)

            individual: person.Person = person.Person(self.__display, person_id,
                                       home_location, office_location, home_position,
                                       home_radius, office_radius,
                                       home_to_office_route, speed, leave_home, status,
                                       self.__disease, self.__disease.get_incubation_time(),
                                       self.__seconds_per_hour, self.__delta_time)

            self.__tilemap.get_home_from_location(home_location).add_occupant(individual)
            self.__tilemap.get_office_from_location(office_location).add_occupant(individual)
            individual.set_office_position(self.__calculate_office_position(person_id,
                                                                            office_location,
                                                                            office_location_dist_dict))

            people.append(individual) # Add person to list of people

        return people

    def __calculate_status(self, person_id: int, infected_person_id: int) -> str:
        """'I' for the seed-infected person, 'S' for everyone else."""
        return 'I' if person_id == infected_person_id else 'S'

    def __calculate_leave_home(self, time_to_travel: float) -> int:
        """Hour to leave home so the person arrives at the office by 9am (clamped to 1)."""
        leave_home: int = 9 - math.ceil(time_to_travel)
        return max(leave_home, 1)

    def __calculate_time_to_travel(self, route_weight: float, speed: float) -> float:
        """Travel time across a route, expressed in simulated hours."""
        return math.ceil(route_weight / speed) / self.__seconds_per_hour

    def __calculate_speed(self) -> float:
        """Per-tick movement speed in pixels, scaled so traversal time is roughly display-independent."""
        return math.floor((self.__display.get_width() * (60 / self.__fps))
                          / ((2 * self.__building_width) * self.__seconds_per_hour))

    def __scale_xy_list(self, xylist: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Convert tile (x, y) coords to centred pixel coords on the display."""
        scaled_xy_list: list[tuple[int, int]] = []
        for x, y in xylist:
            scaled_x: int = x * self.__building_width + self.__building_width // 2
            scaled_y: int = y * self.__building_height + self.__building_height // 2
            scaled_xy_list.append((scaled_x, scaled_y))
        return scaled_xy_list

    def __calculate_home_location(self, person_id: int, num_in_house: int) -> tuple[int, int]:
        # Person IDs are assigned to houses in blocks of `num_in_house`
        return self.__tilemap.get_houses()[person_id // num_in_house].get_location()

    def __calculate_office_location(self, person_id: int,
                                    office_location_dist: list[tuple[int, int]]) -> tuple[int, int]:
        return office_location_dist[person_id]

    def __calculate_home_position(self, person_id: int,
                                  num_in_house: int,
                                  home_location: tuple[int, int]) -> tuple[int, int]:
        """Pixel position of this person inside their house, chosen from a grid of slots."""
        positions: list[tuple[int, int]] = self.__calculate_positions(num_in_house, home_location)
        return positions[person_id % num_in_house]

    def __calculate_office_position(self, person_id: int,
                                    office_location: tuple[int, int],
                                    office_location_dist_dict: dict[tuple[int, int], int]) -> tuple[int, int]:
        """Pixel position of this person inside their office, indexed by their slot among occupants."""
        num_in_office: int = office_location_dist_dict[office_location]
        positions: list[tuple[int, int]] = self.__calculate_positions(num_in_office, office_location)
        occupants: list[person.Person] = self.__tilemap.get_office_from_location(office_location).get_occupants()

        # Position is decided by order added to occupants list - keeps positions unique
        for index, individual in enumerate(occupants):
            if individual.get_person_id() == person_id:
                return positions[index]

        raise RuntimeError(f"Person ID {person_id} not found in occupants of office at location {office_location}")

    def __calculate_office_location_dist(self, num_people: int) -> list[tuple[int, int]]:
        """List of length `num_people` mapping each ID to an office location, evenly distributed."""
        office_location_dist: list[tuple[int, int]] = []
        num_offices: int = len(self.__tilemap.get_offices())
        people_dist_in_offices: list[int] = self.__calculate_people_dist_in_offices(num_people, num_offices)

        for index, num in enumerate(people_dist_in_offices):
            office_location: tuple[int, int] = self.__tilemap.get_offices()[index].get_location()
            for _ in range(num):
                office_location_dist.append(office_location)
        return office_location_dist

    def __calculate_people_dist_in_offices(self, num_people: int, num_offices: int) -> list[int]:
        """Spread people as evenly as possible across offices; the first `extra_people` get one more."""
        base_allocation: int = num_people // num_offices
        extra_people: int = num_people % num_offices
        distribution: list[int] = [base_allocation] * num_offices
        for i in range(extra_people):
            distribution[i] += 1
        return distribution

    def __calculate_positions(self, num_in_building: int, building_location: tuple[int, int]) -> list[tuple[int, int]]:
        """Grid of slot positions inside a building so occupants don't overlap visually."""
        # ceil(sqrt) gives the smallest square grid that fits num_in_building slots
        divisions: int = math.ceil(math.sqrt(num_in_building))
        x_location, y_location = building_location

        x_offset: float = self.__building_width / (divisions + 1)
        y_offset: float = self.__building_height / (divisions + 1)
        positions: list[tuple[int, int]] = []
        for i in range(divisions):
            col: int = i + 1
            for j in range(divisions):
                row: int = j + 1
                x: int = round((x_location * self.__building_width) + (x_offset * row))
                y: int = round((y_location * self.__building_height) + (y_offset * col))
                positions.append((x, y))
        return positions

    def __convert_list_to_dict(self, input_list: list[tuple[int, int]]) -> dict[tuple[int, int], int]:
        """Count occurrences of each item in `input_list`."""
        dictionary: dict[tuple[int, int], int] = {}
        for key in input_list:
            dictionary[key] = dictionary.get(key, 0) + 1
        return dictionary

    def __calculate_radius(self, num_in_building: int) -> int:
        """Drawing radius that fits `num_in_building` people into a single building tile without overlap."""
        default_radius: int = min(self.__building_width, self.__building_height) // 10
        divisions: int = math.ceil(math.sqrt(num_in_building))
        even_radius: int = min(self.__building_width, self.__building_height) // (2 * (divisions + 1))
        return min(default_radius, even_radius)
