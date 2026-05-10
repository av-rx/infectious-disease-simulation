"""
Defines MST class which creates the MST from a graph.

Imports:
    math
    numpy
    create_graph: Creates a graph as an adjacency list from the map array.
    additional_connections: Adds additional roads to network.

Classes:
    MST
"""

import math
import numpy as np
from . import additional_connections
from . import create_graph

class MST:
    """
    A class to create a MST using Kruskal's algorithm with an adjacency list.

    Attributes:
        __graph (dict[tuple[int, int], list[tuple[int, int]]]): The graph as an adjacency list.
        __edges (list[tuple[int, tuple[int, int], tuple[int, int]]])): List of edges with weights.
        __parent (dict[tuple[int, int], tuple[int, int]])): Dictionary of each node's parent.
        __rank (dict[tuple[int, int], int]): Dictionary to keep track of the rank of each node.
    """
    def __init__(self, map_array: np.ndarray) -> None:
        """
        Intialises the MST class with the given map.

        Args:
            map_array (np.ndarray): A 2D array representing the tilemap.
        """
        # Create the graph from the map
        self.__graph: dict[tuple[int, int], # Create the graph from the map
                           list[tuple[int, int]]] = self.__swap_coordinates(create_graph.CreateGraph(map_array).make_graph())
        # Create a list of edges with weights
        self.__edges: list[tuple[int, tuple[int, int],
                                 tuple[int, int]]] = self.__create_edge_list()
        # Initialise the parent dictionary for union-find
        self.__parent: dict[tuple[int, int], tuple[int, int]] = {}
        # Initialise the rank dictionary for union-find
        self.__rank: dict[tuple[int, int], int] = {}

    def __swap_coordinates(self, graph: dict[tuple[int, int],
                                             list[tuple[int, int]]]) -> dict[tuple[int, int],
                                                                             list[tuple[int, int]]]:
        """
        Swap the coordinates of every node and neighbour in the given graph.

        NOTE: Swapped x, y coordinates due to differences in pygame coordinate system.

        Args:
            graph (dict[tuple[int, int], list[tuple[int, int]]]): The input graph to swap coordinates.

        Returns:
            dict[tuple[int, int], list[tuple[int, int]]]: Graph with swapped coordinates for nodes and neighbours.
        """
        swapped_graph: dict[tuple[int, int], list[tuple[int, int]]] = {}

        for node, neighbours in graph.items():
            swapped_node: tuple[int, int] = (node[1], node[0]) # Swap coordinates
            swapped_neighbours: list[tuple[int, int]] = []
            for neighbour in neighbours:
                swapped_neighbours.append((neighbour[1], neighbour[0])) # Add swapped coordinates to list
            swapped_graph[swapped_node] = swapped_neighbours

        return swapped_graph

    def __create_edge_list(self) -> list[tuple[int, tuple[int, int], tuple[int, int]]]:
        """
        Convert the adjacency list to a list of edges with weights.

        Returns:
            list[tuple[int,
                       tuple[int, int],
                       tuple[int, int]]]: List of tuples with weight, start node, end node of edge.
        """
        edges: list[tuple[int, tuple[int, int], tuple[int, int]]] = [] # Initialise edges list
        for node, neighbours in self.__graph.items(): # Iterate through graph
            for neighbour in neighbours:
                weight: int = self.__calculate_weight(node, neighbour) # Calculate weight of edge
                edges.append((weight, node, neighbour)) # Add the edge to the list

        return edges

    def __calculate_weight(self, node1: tuple[int, int], node2: tuple[int, int]) -> int:
        """
        Calculate the weight (distance) between two nodes.

        Args:
            node1 (tuple[int, int]): Coordinates of the first node.
            node2 (tuple[int, int]): Coordinates of the second node.

        Returns:
            int: Weight (distance) between the two nodes.
        """
        # Calculate the Euclidean distance
        weight: int = int(math.sqrt((node1[0] - node2[0]) ** 2 + (node1[1] - node2[1]) ** 2))
        return weight

    def __find(self, node: tuple[int, int]) -> tuple[int, int]:
        """
        Finds the root of the set which contains the node.
        Uses path compression to flatten tree structure, making future operations more efficient.
        When root found, self.__parent[node] updated to point to root (path compression)

        Args:
            node (tuple[int, int]): Node to find the root of.
        
        Returns:
            tuple[int, int]: Root of the set containing the node.
        """
        if self.__parent[node] != node: # If node not the root
            self.__parent[node] = self.__find(self.__parent[node]) # Recursively call on node's parent until root found

        return self.__parent[node] # Returns root of the set containing original node

    def __union(self, node1: tuple[int, int], node2: tuple[int, int]) -> None:
        """
        Merges two disjoint sets into a single set.

        Args:
            node1 (tuple[int, int]): The first node.
            node2 (tuple[int, int]): The second node.
        """
        root1: tuple[int, int] = self.__find(node1) # Find root of set containing node1
        root2: tuple[int, int] = self.__find(node2) # Find root of set containing node2

        if self.__rank[root1] > self.__rank[root2]: # root1 rank higher than root2
            self.__parent[root2] = root1 # root1 made parent of root2 => root2 now points to root1
        elif self.__rank[root1] < self.__rank[root2]: # root2 rank higher than root1
            self.__parent[root1] = root2 # root2 made parent of root1 => root1 now points to root2
        else: # root1 and root2 are equal rank
            self.__parent[root2] = root1 # root1 made parent of root2
            self.__rank[root1] += 1 # root1 rank (height of tree with root root1) increased by 1

    def __kruskal(self) -> dict[tuple[int, int], list[tuple[tuple[int, int], int]]]:
        """
        Carry out Kruskal's algorithm to find the MST.

        Returns:
            dict[tuple[int, int], 
                 list[tuple[tuple[int, int],
                 int]]]: The MST represented as an adjacency list.
        """
        # Initialise empty dictionary for MST
        mst: dict[tuple[int, int],
                  list[tuple[tuple[int, int], int]]] = {}

        for node in self.__graph: # Iterate through graph
            self.__parent[node] = node # Intialise each node's parent to itself
            self.__rank[node] = 0 # Initialise each node's rank to 0

        self.__edges.sort() # Sort edges by weight

        for edge in self.__edges: # Iterate through edges
            weight, node1, node2 = edge
            if self.__find(node1) != self.__find(node2): # If node1 and node2 are in different sets
                self.__union(node1, node2) # Merge the sets containing node1 and node2
                if node1 not in mst:
                    mst[node1] = [] # List for node1 if it doesn't exist
                if node2 not in mst:
                    mst[node2] = [] # List for node2 if it doesn't exist
                mst[node1].append((node2, weight)) # Add edge to MST
                mst[node2].append((node1, weight)) # Add edge to MST

        return mst

    def get_mst(self, additional_roads) -> dict[tuple[int, int], list[tuple[tuple[int, int], int]]]:
        """
        Get the MST of the graph.

        Returns:
            dict[tuple[int, int],
                 list[tuple[tuple[int, int],
                 int]]]: MST represented as an adjacency list.
        """
        if additional_roads:
            # Result of Kruskal's algorithm taken and additional connections found using it
            return additional_connections.AdditionalConnections(self.__kruskal()).add_connections()
        return self.__kruskal() # Run Kruskal's algorithm and return the MST
