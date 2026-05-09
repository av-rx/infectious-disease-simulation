"""
Defines CreateGraph class which creates a graph as an adjacency list from a 2D array.

Imports:
    numpy

Classes:
    CreateGraph
"""
import numpy as np

class CreateGraph:
    """
    A class to create a graph as an adjacency list from a 2D array (the map).

    Attributes:
        __map (np.ndarray): A 2D array representing the tilemap.
    """
    def __init__(self, map_array: np.ndarray) -> None:
        """
        Initialises the CreateGraph class with the given map.

        Args:
            map_array (np.ndarray): A 2D array representing the tilemap.
        """
        self.__map: np.ndarray = map_array

    def make_graph(self) -> dict[tuple[int, int], list[tuple[int, int]]]:
        """
        Creates a graph where each building is a node and edges connect to nearby buildings.

        Returns:
            dict[tuple[int, int],
                 list[tuple[int, int]]]: Dictionary representing graph.
                                         Keys are nodes, and values are lists of neighbouring nodes.
        """
        rows: int = len(self.__map)
        columns: int = len(self.__map[0])
        graph: dict[tuple[int, int], list[tuple[int, int]]] = {}
        points: list[tuple[int, int]] = []
        k: int = max(3, int(len(points) ** 0.5)) # Heuristic for number of neighbours
        k = min(k, 6) # Limit k to max 6

        # Collect building tiles
        for i in range(rows):
            for j in range(columns):
                if self.__map[i][j] != 0:
                    points.append((i, j))

        # For each building, find its nearest neighbours
        for px, py in points:
            distances: list[tuple[int, tuple[int, int]]] = []
            # Compare current building to every other building
            for qx, qy in points:
                if (px, py) == (qx, qy): # Do not connect building to itself
                    continue
                
                # Calculate distance (squared to avoid sqrt for efficiency)
                dx = px - qx
                dy = py - qy
                distance_squared = dx * dx + dy * dy
                distances.append((distance_squared, (qx, qy))) # Store distance and corresponding neighbour
            
            # Sort neighbours by distance
            distances.sort(key=lambda item: item[0])

            # Take the K nearest neighbours
            neighbours: list[tuple[int, int]] = []
            limit = min(k, len(distances)) # May have fewer than K neighbours
            for i in range(limit):
                neighbours.append(distances[i][1])
            graph[(px, py)] = neighbours # Assign neighbour list to graph

        return graph
