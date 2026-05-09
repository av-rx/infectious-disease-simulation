"""
Population: collective state and per-tick update for every Person in the simulation.
"""
import math
import random
from .initialise_people import InitialisePeople
from ..display import Display # For typing
from ..world import create_map # For typing
from ..world import tilemap # For typing
from ..simulation import disease # For typing
from ..agents import person # For typing

class Population:
    """Owns the list of people, their commute-route intersections, and per-tick updates."""
    def __init__(self, num_in_house: int,
                 display_obj: Display,
                 map_obj: create_map.CreateMap,
                 disease_obj: disease.Disease,
                 seconds_per_hour: float, fps: int,
                 rng: random.Random | None = None) -> None:
        """
        Args:
            num_in_house: Number of people per house.
            display_obj: Display surface (real or headless).
            map_obj: The map (provides tilemap and roads).
            disease_obj: Shared Disease instance for transmission rolls.
            seconds_per_hour: Real seconds per simulated hour.
            fps: Display frames per second.
            rng: Optional injected RNG, threaded into population init.
        """
        self.__display: Display = display_obj
        self.__map: create_map.CreateMap = map_obj
        self.__tilemap: tilemap.Tilemap = self.__map.get_tilemap()
        self.__num_in_house: int = num_in_house
        self.__disease: disease.Disease = disease_obj
        self.__seconds_per_hour: float = seconds_per_hour
        self.__fps: int = fps
        self.__delta_time: float = 1 / self.__fps
        self.__people: list[person.Person] = InitialisePeople(self.__num_in_house,
                                                              self.__display,
                                                              self.__map,
                                                              self.__disease,
                                                              self.__seconds_per_hour,
                                                              self.__fps,
                                                              rng=rng).get_people()
        self.__route_intersections: dict[int, list[person.Person]] = self.__find_route_intersections()

    def draw_people(self) -> None:
        for individual in self.__people:
            individual.draw_person()

    def get_people(self) -> list[person.Person]:
        return self.__people

    def move_to_offices(self) -> None:
        for individual in self.__people:
            individual.start_move_to_office()

    def move_to_homes(self) -> None:
        for individual in self.__people:
            individual.start_move_to_home()

    def update_positions(self) -> None:
        """Move each person and roll for in-transit infection."""
        for individual in self.__people:
            individual.update_position()
            self.__check_interactions(individual)

    def update_infection_status(self) -> None:
        """Roll for in-building infection then advance every person's disease state."""
        self.__check_building_interactions()
        for individual in self.__people:
            individual.update_infection_status()

    def has_active_infections(self) -> bool:
        """True if anyone is exposed (E) or infected (I)."""
        for individual in self.__people:
            if individual.get_status() in ("E", "I"):
                return True
        return False

    def get_status_counts(self) -> dict[str, int]:
        """Tally of S/E/I/R/D for the live graph."""
        counts: dict[str, int] = {'S': 0, 'E': 0, 'I': 0, 'R': 0, 'D': 0}
        for individual in self.__people:
            counts[individual.get_status()] += 1
        return counts

    def __find_route_intersections(self) -> dict[int, list[person.Person]]:
        """
        Map each person to the set of others whose commute route shares at least one tile.

        Used as an optimisation: only people on overlapping routes can infect each other in transit,
        so the per-tick interaction check iterates over this much smaller list instead of all pairs.
        """
        # Bucket people by tile, then for each person union the buckets of every tile on their route
        tile_buckets: dict[tuple[int, int], list[person.Person]] = {}
        person_route_sets: dict[int, set[tuple[int, int]]] = {}

        for individual in self.__people:
            pid: int = individual.get_person_id()
            route_tiles: set[tuple[int, int]] = set(individual.get_home_to_office_route())
            person_route_sets[pid] = route_tiles
            for tile in route_tiles:
                tile_buckets.setdefault(tile, []).append(individual)

        intersections: dict[int, list[person.Person]] = {}
        for individual in self.__people:
            pid = individual.get_person_id()
            others_set: set[person.Person] = set()
            for tile in person_route_sets[pid]:
                for other in tile_buckets.get(tile, []):
                    if other is not individual:
                        others_set.add(other)
            # Sort by person_id so iteration order is deterministic across runs.
            # (Default Person hash is id()-based, so list(set) order varies between processes
            # and would desync any seeded run.)
            intersections[pid] = sorted(others_set, key=lambda p: p.get_person_id())

        return intersections

    def __check_interactions(self, individual: person.Person) -> None:
        """Roll an infection check between an infected person and any susceptible they touch on a shared route."""
        if individual.get_status() != "I":
            return
        for other in self.__route_intersections[individual.get_person_id()]:
            if other.get_status() != "S":
                continue
            distance = self.__calculate_distance(individual.get_current_position(),
                                                 other.get_current_position())
            if distance <= 2 * individual.get_radius() and self.__disease.infect(self.__delta_time):
                other.set_status("E")

    def __check_building_interactions(self) -> None:
        """Roll infection checks for every infected person against other occupants of their current building."""
        for individual in self.__people:
            if individual.get_status() != "I":
                continue

            # Only contagious indoors, not while commuting
            if individual.get_current_position() == individual.get_home_position():
                occupants = self.__tilemap.get_home_from_location(individual.get_home_location()).get_occupants()
            elif individual.get_current_position() == individual.get_office_position():
                occupants = self.__tilemap.get_office_from_location(individual.get_office_location()).get_occupants()
            else:
                continue

            for occupant in occupants:
                if occupant.get_status() == "S" and self.__disease.infect(self.__delta_time):
                    occupant.set_status("E")

    def __calculate_distance(self, pos1: tuple[int, int], pos2: tuple[int, int]) -> float:
        return math.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
