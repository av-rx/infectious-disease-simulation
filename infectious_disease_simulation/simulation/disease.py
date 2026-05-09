"""
Disease model: converts daily probabilities to per-second hazards and rolls events.
"""

import random
import math

class Disease:
    """
    SEIRD transition probabilities for the simulation.

    Daily probabilities (infection/recovery/mortality) are converted once into per-real-second
    hazards (lambdas) at construction. Per-tick checks then use the standard exponential
    formula `1 - exp(-lambda * dt)`.
    """
    def __init__(self, infection_rate: float, incubation_time: float,
                 recovery_rate: float, mortality_rate: float,
                 seconds_per_hour: float, rng: random.Random | None = None) -> None:
        """
        Args:
            infection_rate: Daily probability of a contact infecting a susceptible (0..1).
            incubation_time: Incubation period in simulated days.
            recovery_rate: Daily probability of an infected person recovering (0..1).
            mortality_rate: Daily probability of an infected person dying (0..1).
            seconds_per_hour: Real seconds per simulated hour.
            rng: Optional injected RNG for deterministic tests.
        """
        self.__infection_rate: float = float(infection_rate)
        self.__incubation_time: float = float(incubation_time)
        self.__recovery_rate: float = float(recovery_rate)
        self.__mortality_rate: float = float(mortality_rate)
        self.__seconds_per_hour: float = float(seconds_per_hour)
        self.__rng: random.Random = rng or random.Random()

        self.__lambda_infect = self.__daily_to_lambda(self.__infection_rate)
        self.__lambda_recover = self.__daily_to_lambda(self.__recovery_rate)
        self.__lambda_die = self.__daily_to_lambda(self.__mortality_rate)
        self.__incubation_time = self.__incubation_time * 24 * self.__seconds_per_hour

    def __daily_to_lambda(self, prob: float) -> float:
        """Convert a daily probability to a per-real-second hazard rate (lambda)."""
        # p_day = 1 - exp(-lambda * 24 * seconds_per_hour)
        if prob <= 0:
            return 0.0
        if prob >= 1:
            return float('inf')
        denominator: float = 24 * self.__seconds_per_hour
        return -math.log(1.0 - prob) / denominator

    def __happens(self, lambda_rate: float, delta_time: float) -> bool:
        """Roll an event with hazard `lambda_rate` over `delta_time` real seconds."""
        if lambda_rate == 0.0:
            return False
        if math.isinf(lambda_rate):
            return delta_time > 0.0
        prob: float = 1.0 - math.exp(-lambda_rate * delta_time)
        return self.__rng.random() < prob

    def infect(self, delta_time: float) -> bool:
        """True if a susceptible-infected contact transmits over `delta_time` seconds."""
        return self.__happens(self.__lambda_infect, delta_time)

    def recover(self, delta_time: float) -> bool:
        """True if an infected person recovers over `delta_time` seconds."""
        return self.__happens(self.__lambda_recover, delta_time)

    def die(self, delta_time: float) -> bool:
        """True if an infected person dies over `delta_time` seconds."""
        return self.__happens(self.__lambda_die, delta_time)

    def get_incubation_time(self) -> float:
        """Incubation period in real seconds."""
        return self.__incubation_time
