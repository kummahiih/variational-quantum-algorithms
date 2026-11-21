"""Budgeted angle-grid search: a global prefix followed by one local pattern search."""

from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from math import floor, isfinite, pi
from random import Random

from dyadic_sieve import keys as original_keys
from pattern_search import ENERGY_TOLERANCE, pattern_polls
from recursive_dyadic_sieve import keys as recursive_keys
from sieve_qaoa import qaoa_energy

Point = tuple[int, int]
STARTERS = ("original", "recursive", "halton", "sobol", "random",
            "original_coordinate", "recursive_coordinate")


def _morton_point(key: int, bits: int) -> Point:
    """Split alternating key bits between the two axes; the top bit goes to gamma."""
    gamma = beta = 0
    for index in range(bits):
        gamma |= ((key >> (2 * index + 1)) & 1) << index
        beta |= ((key >> (2 * index)) & 1) << index
    return gamma, beta


def _radical_cell(index: int, base: int, size: int) -> int:
    numerator, denominator = 0, 1
    while index:
        index, digit = divmod(index, base)
        numerator = numerator * base + digit
        denominator *= base
    return size * numerator // denominator


def _halton_cells(size: int) -> Iterator[Point]:
    seen = {(0, 0)}
    index = 1
    while len(seen) < size * size:
        point = _radical_cell(index, 2, size), _radical_cell(index, 3, size)
        index += 1
        if point not in seen:
            seen.add(point)
            yield point


def _sobol_cells(bits: int) -> Iterator[Point]:
    """Unscrambled 2-D Sobol sequence, floored onto the grid; omit the origin."""
    width = 2 * bits
    vx = [1 << (width - 1 - j) for j in range(width)]
    vy = [vx[0]]
    for _ in range(1, width):  # second dimension: primitive polynomial x + 1
        vy.append(vy[-1] ^ (vy[-1] >> 1))
    x = y = 0
    for i in range(1, 1 << width):
        j = (i & -i).bit_length() - 1
        x ^= vx[j]
        y ^= vy[j]
        yield x >> bits, y >> bits


def _random_cells(size: int, seed: int) -> Iterator[Point]:
    """Lazy Fisher-Yates draw over the nonzero cell indices."""
    rng = Random(seed)
    swaps: dict[int, int] = {}
    for last in range(size * size - 1, 0, -1):
        selected = rng.randint(1, last)
        cell = swaps.get(selected, selected)
        swaps[selected] = swaps.get(last, last)
        swaps.pop(last, None)
        yield divmod(cell, size)


def _pilot_points(starter: str, bits: int, initial: Point,
                  incumbent: Callable[[], tuple[Point, float]], seed: int) -> Iterator[Point]:
    size = 1 << bits
    if starter.endswith("_coordinate"):
        keys = original_keys if starter == "original_coordinate" else recursive_keys
        while True:
            fixed_beta = incumbent()[0][1]
            for key in keys(bits):
                yield key, fixed_beta
            fixed_gamma = incumbent()[0][0]
            for key in keys(bits):
                yield fixed_gamma, key
    elif starter in ("original", "recursive"):
        keys = original_keys if starter == "original" else recursive_keys
        # Both key orders end in zero. The common start already pays for it.
        offsets = (_morton_point(key, bits) for key in keys(2 * bits) if key)
    elif starter == "halton":
        offsets = _halton_cells(size)
    elif starter == "sobol":
        offsets = _sobol_cells(bits)
    else:
        offsets = _random_cells(size, seed)
    for x, y in offsets:
        yield (initial[0] + x) % size, (initial[1] + y) % size


@dataclass(frozen=True)
class Trial:
    point: Point
    energy: float
    incumbent: Point
    best_energy: float


@dataclass(frozen=True)
class CheckpointSwitch:
    """At call 8 elect to poll now or use the remainder of the pilot allowance."""
    switch_if_improving: bool
    switch_if_stale: bool

    def __call__(self, history: Sequence[Trial]) -> bool:
        if len(history) != 8:
            return False
        improving = history[-1].best_energy < history[3].best_energy - ENERGY_TOLERANCE
        return self.switch_if_improving if improving else self.switch_if_stale


@dataclass(frozen=True)
class HybridTrace:
    angle_bits: int
    pilot_calls: int
    trials: tuple[Trial, ...]

    @property
    def best_angles(self) -> tuple[float, float]:
        gamma, beta = self.trials[-1].incumbent
        step = 2 * pi / (1 << self.angle_bits)
        return gamma * step, beta * step

    @property
    def best_energy(self) -> float:
        return self.trials[-1].best_energy

    def first_hit(self, target: float) -> int | None:
        if not isfinite(target):
            raise ValueError("target must be finite")
        return next((t for t, trial in enumerate(self.trials, 1)
                     if trial.best_energy <= target + ENERGY_TOLERANCE), None)


def search_grid(
    objective: Callable[[int, int], float], *, angle_bits: int = 4,
    max_evaluations: int = 65, initial: Point | None = None,
    starter: str = "halton", pilot_fraction: float = 0.2,
    patience: int | None = None, seed: int = 0,
    switch_when: Callable[[Sequence[Trial]], bool] | None = None,
) -> HybridTrace:
    """Minimize an objective on a periodic square grid of side 2**angle_bits.

    Initial is a pair of integer grid indices. The rounded pilot allowance
    includes its evaluation (at least one). With patience set, also switch
    after that many consecutive pilot calls without a strict improvement.
    Fraction zero gives local-only, one gives pilot-only when patience is None.
    An optional switch_when(history) can hand off after any paid pilot call.
    All objective calls count, including repeated local or coordinate polls.
    A finite joint schedule can exhaust its grid; a local search can converge
    before the cap. The handoff reuses the evaluated incumbent for free.
    """
    if not isinstance(angle_bits, int) or angle_bits < 1:
        raise ValueError("angle_bits must be a positive integer")
    if not isinstance(max_evaluations, int) or max_evaluations < 1:
        raise ValueError("max_evaluations must be a positive integer")
    if starter not in STARTERS:
        raise ValueError(f"starter must be one of {STARTERS}")
    if not 0 <= pilot_fraction <= 1:
        raise ValueError("pilot_fraction must be in [0, 1]")
    if patience is not None and (not isinstance(patience, int) or patience < 1):
        raise ValueError("patience must be a positive integer")
    size = 1 << angle_bits
    if initial is None:
        initial = size // 8, size // 16
    if len(initial) != 2 or not all(isinstance(x, int) and 0 <= x < size for x in initial):
        raise ValueError("initial must contain two integer grid indices in range")

    best, best_energy = initial, float("inf")
    trials: list[Trial] = []

    def incumbent() -> tuple[Point, float]:
        return best, best_energy

    def evaluate(point: Point) -> bool:
        nonlocal best, best_energy
        wrapped = point[0] % size, point[1] % size
        energy = float(objective(*wrapped))
        if not isfinite(energy):
            raise ValueError("objective returned a nonfinite energy")
        improved = energy < best_energy - ENERGY_TOLERANCE
        if improved:
            best, best_energy = wrapped, energy
        trials.append(Trial(wrapped, energy, best, best_energy))
        return improved

    evaluate(initial)
    allowance = max(1, floor(max_evaluations * pilot_fraction + 0.5))
    stale = 0
    if allowance > 1 and not (switch_when and switch_when(tuple(trials))):
        for point in _pilot_points(starter, angle_bits, initial, incumbent, seed):
            improved = evaluate(point)
            stale = 0 if improved else stale + 1
            if (len(trials) >= allowance or stale == patience or
                    (switch_when is not None and switch_when(tuple(trials)))):
                break
    pilot_calls = len(trials)
    pure_pilot = allowance == max_evaluations and patience is None and switch_when is None
    if not pure_pilot and pilot_calls < max_evaluations:
        for point in pattern_polls(incumbent, angle_bits, 1):
            evaluate(point)
            if len(trials) == max_evaluations:
                break
    return HybridTrace(angle_bits, pilot_calls, tuple(trials))


def optimize_hybrid(
    costs: Sequence[float], *, angle_bits: int = 4, max_evaluations: int = 65,
    initial: Point | None = None, starter: str = "halton", pilot_fraction: float = 0.2,
    patience: int | None = None, seed: int = 0,
    switch_when: Callable[[Sequence[Trial]], bool] | None = None,
) -> HybridTrace:
    """Run the hybrid on the exact p=1 QAOA statevector. Angles returned in radians."""
    if not isinstance(angle_bits, int) or angle_bits < 1:
        raise ValueError("angle_bits must be a positive integer")
    step = 2 * pi / (1 << angle_bits)
    return search_grid(lambda g, b: qaoa_energy(costs, g * step, b * step),
                       angle_bits=angle_bits, max_evaluations=max_evaluations, initial=initial,
                       starter=starter, pilot_fraction=pilot_fraction, patience=patience, seed=seed,
                       switch_when=switch_when)
