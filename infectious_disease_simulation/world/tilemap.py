"""
Tilemap: random placement of houses and offices onto a grid of tile cells.
"""
import random
import numpy as np
import pygame
from .buildings import Building, House, Office
from ..display import Display

class Tilemap:
    """Random building placement on a grid sized by display_size / building_size."""
    def __init__(self, display_obj: Display,
                 num_houses: int, num_offices: int,
                 building_width: int, building_height: int,
                 rng: random.Random | None = None) -> None:
        """
        Args:
            display_obj: Display surface (real or headless).
            num_houses: Number of House tiles to place.
            num_offices: Number of Office tiles to place.
            building_width: Width of each building tile in pixels.
            building_height: Height of each building tile in pixels.
            rng: Optional injected RNG for deterministic placement.
        """
        self.__display: Display = display_obj
        self.__building_width: int = building_width
        self.__building_height: int = building_height
        self.__size: tuple[int, int] = (int(self.__display.get_width() / building_width),
                                        int(self.__display.get_height() / building_height))
        self.__map: np.ndarray = np.zeros(self.__size, dtype=int)
        self.__houses_list: list[House] = []
        self.__offices_list: list[Office] = []
        self.__houses_dict: dict[tuple[int, int], House] = {}
        self.__offices_dict: dict[tuple[int, int], Office] = {}
        self.__buildings: list[Building] = []
        self.__num_houses: int = num_houses
        self.__num_offices: int = num_offices
        self.__current_houses: int = 0
        self.__current_offices: int = 0
        self.__rng: random.Random = rng or random.Random()

    def get_num_houses(self) -> int:
        """
        Returns the number of houses to be placed on the tilemap.

        Returns:
            int: The number of houses to be placed.
        """
        return self.__num_houses

    def get_houses(self) -> list[House]:
        """
        Returns the list of houses placed on the tilemap.
        
        Returns:
            list[House]: The list of houses.
        """
        return self.__houses_list

    def get_offices(self) -> list[Office]:
        """
        Returns the list of offices placed on the tilemap.
        
        Returns:
            list[Office]: The list of offices.
        """
        return self.__offices_list
    
    def get_houses_dict(self) -> dict[tuple[int, int], House]:
        """
        Returns the dictionary mapping locations to House objects in the tilemap.

        Returns:
            dict[tuple[int, int], House]: The dictionary of houses by location.
        """
        return self.__houses_dict
    
    def get_offices_dict(self) -> dict[tuple[int, int], Office]:
        """
        Returns the dictionary mapping locations to Office objects in the tilemap.

        Returns:
            dict[tuple[int, int], Office]: The dictionary of offices by location.
        """
        return self.__offices_dict

    def get_buildings(self) -> list[Building]:
        """
        Returns the list of buildings placed on the tilemap.
        
        Returns:
            list[Building]: The list of buildings.
        """
        return self.__buildings

    def get_home_from_location(self, location: tuple[int, int]) -> House:
        """
        Returns the house object from a coordinate location.

        Returns:
            House: The House object with the required location.
        """
        try:
            return self.__houses_dict[location]
        except KeyError:
            raise RuntimeError(f"No house found at location {location}")

    def get_office_from_location(self, location: tuple[int, int]) -> Office:
        """
        Returns the office object from a coordinate location.

        Returns:
            Office: The Office object with the required location.
        """
        try:
            return self.__offices_dict[location]
        except KeyError:
            raise RuntimeError(f"No office found at location {location}")

    def get_map(self) -> np.ndarray:
        """
        Returns the state of the tilemap as an array.
        
        Returns:
            np.ndarray: A 2D array representing the tilemap.
        """
        return self.__map

    def get_building_width(self) -> int:
        """
        Returns the width of a building in the tilemap (pixels).

        Returns:
            int: The building width
        """
        return self.__building_width

    def get_building_height(self) -> int:
        """
        Returns the height of a building in the tilemap (pixels).

        Returns:
            int: The building height
        """
        return self.__building_height

    def __place_building(self, building_cls: Building, empty_locations: list[tuple[int, int]]) -> None:
        """
        Places a building of the specified type on the tilemap at a random, empty location.
        If location not empty, random values generated until an empty location is found.

        Args:
            building_cls (Building): The type of building ofbject to place.
            empty_locations (list[tuple[int, int]]): List of available empty locations on the tilemap.
        """
        # No empty locations available
        if not empty_locations:
            return
        
        x, y = self.__rng.choice(empty_locations)
        building = building_cls((x, y))

        # NOTE
        # [x, y] flipped due to differences in coordinate systems in Python/ NumPy and Pygame
        # Python/ NumPy: first index = row (y), second index = column (x)
        # Pygame: first index = column (x), second index = row (y)
        if isinstance(building, House) and self.__current_houses < self.__num_houses:
            self.__houses_dict[building.get_location()] = building # Store house by location for fast lookup
            self.__houses_list.append(building) # Append to list of houses
            self.__current_houses += 1
        elif isinstance(building, Office) and self.__current_offices < self. __num_offices:
            self.__offices_dict[building.get_location()] = building # Store office by location for fast lookup
            self.__offices_list.append(building) # Append to list of offices
            self.__current_offices += 1
        else:
            return # Do not place building if max count reached
        
        self.__buildings.append(building) # Add to list of buildings
        self.__map[y, x] = building.get_tile_value() # Update tilemap array
        empty_locations.remove((x, y))

    def render(self, pause: bool) -> None:
        """
        Renders all buildings on the display.
        Draws each building as a rectangle on the display surface using its location and dimensions.

        Args:
            pause (bool): True if display process to be shown, False if not.
        """
        # Get empty locations on the tilemap
        empty_locations: list[tuple[int, int]] = [(x, y)
                                                  for x in range(self.__size[0])
                                                  for y in range(self.__size[1])
                                                  if self.__map[y, x] == 0]

        # Loop through number of houses, offices and place on tilemap
        for building_cls, max_count in [(House, self.__num_houses),
                                        (Office, self.__num_offices),]:
            for _ in range(max_count):
                self.__place_building(building_cls, empty_locations)

        for building in self.__buildings:
            x, y = building.get_location()
            pygame.draw.rect(self.__display.get_screen(), # Display surface
                             building.get_colour(), # Colour
                             (x * self.__building_width, # Top left coord
                              y * self.__building_height, # Top right coord
                              self.__building_width, # Bottom left coord
                              self.__building_height)) # Bottom right coord
            if pause:
                self.__display.update()
                pygame.time.wait(2) # Wait to show drawing process
