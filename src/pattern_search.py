"""Four-direction pattern polling, shared by the original and hybrid searches."""

from collections.abc import Callable, Iterator
from typing import TypeVar

Coordinate = TypeVar("Coordinate", int, float)
ENERGY_TOLERANCE = 1e-12


def pattern_polls(
    incumbent: Callable[[], tuple[tuple[Coordinate, Coordinate], float]],
    angle_bits: int,
    grid_step: Coordinate,
) -> Iterator[tuple[Coordinate, Coordinate]]:
    """Yield a poll at a time. The caller evaluates it and updates its incumbent.

    Each group of four polls uses one frozen center. Repeat a successful step
    size, halve it after an unsuccessful group, and stop below one grid unit.
    """
    for exponent in range(angle_bits - 2, -1, -1):
        step = (1 << exponent) * grid_step
        while True:
            (gamma, beta), before = incumbent()
            yield gamma + step, beta
            yield gamma - step, beta
            yield gamma, beta + step
            yield gamma, beta - step
            if incumbent()[1] >= before - ENERGY_TOLERANCE:
                break
