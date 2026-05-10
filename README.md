# Infectious Disease Simulation

## Overview

A program to visualise simulations of an infectious disease spreading through a procedurally generated basic town.

![Simulation Demo Gif](./assets/simulation_demo.gif)
The simulation shown above has been run with default parameters.

This README details (in part) the key components of the program and how they work.

## Run

1. Clone the repository:

    ```bash
    git clone https://github.com/defunctdreams/infectious-disease-simulation.git
    ```

2. Navigate to the directory in which the code is saved:

    ```bash
    cd infectious-disease-simulation
    ```

3. Install poetry (if not already installed):

    ```bash
    pip install poetry
    ```

4. Install project dependencies:

    ```bash
    poetry install
    ```

5. Run the program (GUI):

    ```bash
    poetry run python -m infectious_disease_simulation.main
    ```

6. Set parameters in the `Simulation Parameters` window, or load a previous simulation's parameters by clicking `Load Previous Run`

7. Run the simulation by clicking `Run Simulation`

8. Use the map window to visualise the movement of people and propagation of the disease, and the graph window to see the live S/E/I/R/D curves

### Headless Mode

For automated runs without a GUI (e.g. for batch experiments, regression checks, or testing), use a JSON config file:

```bash
poetry run python -m infectious_disease_simulation.main --headless assets/configs/default_config.json
```

`assets/configs/default_config.json` is provided as a starting point — copy it and tweak the values to define your own scenarios.

In headless mode the simulation runs unthrottled (no real-time pacing), suppresses the live graph, and prints the final day, hour, and S/E/I/R/D counts when the run terminates.

Add `--seed N` for a fully reproducible run; the same seed always produces the same outcome:

```bash
poetry run python -m infectious_disease_simulation.main --headless assets/configs/default_config.json --seed 42
```

### Run with Nix Flakes

The program is wrapped in a flake, so it can be run with:

```bash
nix run 'github:defunctdreams/infectious-disease-simulation'
```

## Development

### Tests

The test suite uses `pytest`. After `poetry install` (which picks up the dev dependency group automatically), run:

```bash
poetry run pytest
```

Tests cover `Config` validation, `Disease` hazard math (with statistical sanity checks), `Dijkstra` and the heap-based `PriorityQueue`, MST construction, `Person` state transitions, and an end-to-end headless smoke test that confirms a seeded run is deterministic.

## About the Project

This project builds a visual simulation of an infectious disease using Python and Pygame.

The map is procedurally generated, with a grid of locations for houses and offices, and roads dynamically created to connect buildings using a MST-based network. People travel between homes and offices using shortest-path routing, and a compartmental SEIRD model is used for the progression of the disease within a person and the population. Properties for the simulation speed, display, map, population, and disease are set at the beginning of the simulation and each have an effect on the simulation.

## Why?

This project was inspired by the COVID-19 pandemic, and the huge impacts that such a tiny particle can have on the world at such large scales.

The project aims to:

- Demonstrate how a disease spreads through a population visually
- Provide users with the ability to create their own, unique simulation scenarious by adjusting parameters
- Balance simplicity with accuracy, so that there is some learning value, whilst being accessible and easy to use

## The Town

### The Buildings

The map is a tilemap grid. Each tile is either empty (no building), or contains a house or office.

Random building placement is used on tile cells until the specified numbers of houses and offices are placed.

### The Roads

All buildings are connected with roads, allowing travel between buildings.

A Minimum Spanning Tree is generated using Kruskal's algorithm. This guarantees that all buildings are connected without unrealistic crisscrossing. It also provides a good base for the road network.

An additional algorithm is used (if selected by the user when running the simulation) which adds additional roads. This provides a slightly more realistic road network.

This algorithm looks at buildings with only one road connection, and looks at other buildings with only one road connection that are more than a certain distance apart (otherwise the network becomes very messy). It then checks if a road between the two buildings would overlap with an existing road. If an overlap does not occur, the road is added to the graph representing the map, and is drawn.

## The People

People live in houses and commute to offices, reaching the office by 9am, and leaving the office by 5pm.

The number of people in each house is specified by the user before running the simulation, and the number of people assigned to each office is distributed as evenly as possible.

Dijsktra's algorithm is used for pathfinding so each person knows which route to take to get from their house to office and vice versa.

## The Disease Model

The simulation uses a stochastic compartmental SEIRD epidemiological model.

The SEIRD model stands for the following:

- (S)usceptible: Healthy individual who can catch the disease
- (E)xposed: Infected but not yet infectious (incubation time)
- (I)nfectious: Infected and infectious
- (R)ecovered: Gained immunity after infection
- (D)eceased: Died after infection

The user provides daily probabilities for infection, recovery, and mortality. These are each converted once at the start of the simulation into a per-second hazard rate using `lambda = -ln(1 - p_day) / (24 * seconds_per_hour)`. Every simulation tick then rolls the event with probability `1 - exp(-lambda * delta_t)` against a uniform random draw. This is the standard way of converting a daily probability into something that fires correctly at any tick rate.

Because the rolls are pseudo-random, two runs with the same parameters produce different trajectories unless a fixed seed is supplied (see [Headless Mode](#headless-mode)). With a seed, the run is fully reproducible, which is what the test suite uses to catch regressions.

The four parameters that drive the model are:

- Infection rate: daily probability of a contact transmitting from an infected person to a susceptible one
- Incubation time: number of days between exposure and becoming infectious
- Recovery rate: daily probability of an infected person recovering
- Mortality rate: daily probability of an infected person dying

## The Clock

The simulation speed can be adjusted before running the simulation.

The internal clock increments the internal time counter and calls population update methods, whilst also triggering the graph to update with new plots.

## The Visualisation

A real-time graph pulls data about the number of people in each compartment, and displays this on another window.

This allows all five curves to be displayed together, making it easy to track all types of cases.

## The Parameters

### The Explanation

| Parameter | Description |
| --------- | ----------- |
| Simulation Name | Name associated with the specific run of the simulation |
| Simulation Speed | Speed at which to run the simulation |
| Display Size | Size of the window to run the simulation in (pixels) |
| Number of Houses | Number of houses included in the map |
| Number of Offices | Number of offices included in the map |
| Building Size | Size of each building in the map (pixels) |
| Number of People per House | Number of people in each house |
| Show Map Drawing Process | Show the drawing process of the map (tiny pauses after each step) |
| Draw Additional Roads | Draw additional roads to connect the road network together (see [Roads](#the-roads)) |
| Infection Rate | Probability of a contact getting infected |
| Incubation Time | Number of days between a person contracting the disease and becoming infectious |
| Recovery Rate | Probability of an infected person recovering |
| Mortality Rate | Probability of an infected person dying |

### The Validation and Warnings

The simulation rejects parameters that would prevent it from running correctly. The same rules apply to GUI submissions and headless config files, so any invalid value is caught before the run starts. The hard validations are:

- The simulation name is non-empty and at most 50 characters
- The simulation speed is positive
- The display size is a positive integer and at most 2160 pixels
- The building size is a positive integer
- There is at least one house and one office
- There are enough tile cells for the requested number of buildings
- The number of people per house is a positive integer
- The infection rate, recovery rate, and mortality rate are decimals between 0 and 1
- The incubation time is not less than 0 days

Warnings (rather than errors) are shown when the parameters are unusual but still runnable — the user can choose to proceed. These are GUI-only prompts; headless runs skip them.

| Warning | Reason |
| ------- | ------ |
| Large population size | Simulation may not run smoothly on all systems |
| Large number of buildings | Road network may take time to generate |
| Recovery rate and mortality rate are 0 | Simulation will not end |
| People too small to render | Population/building-size combination would draw circles below 1 pixel radius |

## The Database

All previous runs are stored in a database, and can be retrieved by clicking the `Load Previous Run` button in the `Simulation Parameters` window.

This opens a window displaying previous runs, and showing the most important parameters of the runs to better help identify the run.

The run can then be selected and loaded, filling the parameters with the parameter values from that simulation run.

## The Future

- [ ] Maps can be saved and reused directly in the program
- [ ] Users can create their own custom maps
- [ ] Additional interventions (vaccinations, lockdowns, etc.)
- [ ] More nuanced human behaviours (mask-wearing, testing, isolation, etc.)
- [ ] Performance optimisations and fixing inefficient iterations
- [ ] Remove recovery bias (model checks for recovery before death)
