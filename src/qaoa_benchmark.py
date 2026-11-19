"""Dependency-free, evaluation-matched benchmarks for one-layer QAOA angles.

An evaluation is one exact statevector probability/energy calculation (not a
physical quantum shot). A trace keeps the best *evaluated* angle pair after
each call, so early-hit rank and budget checkpoints are reproducible.
"""

from dataclasses import dataclass
from math import isfinite, pi
from random import Random
from collections.abc import Sequence

from dyadic_sieve import keys as original_keys
from recursive_dyadic_sieve import keys as recursive_keys
from sieve_qaoa import maxcut_costs, qaoa_probabilities


METHODS = (
    "recursive", "original", "ascending", "shuffled",
    "random_joint", "pattern",
)


@dataclass(frozen=True)
class Observation:
    evaluations: int
    gamma: float
    beta: float
    best_energy: float
    optimal_probability: float


@dataclass(frozen=True)
class BenchmarkTrace:
    method: str
    observations: tuple[Observation, ...]

    @property
    def evaluations(self) -> int:
        return len(self.observations)

    def at_budget(self, budget: int) -> Observation:
        """Best evaluated point within a budget, even if search finished early."""
        if budget < 1:
            raise ValueError("budget must be positive")
        return self.observations[min(budget, self.evaluations) - 1]

    def first_hit(self, target_energy: float) -> int | None:
        """1-based first evaluation attaining the specified expected energy."""
        if not isfinite(target_energy):
            raise ValueError("target_energy must be finite")
        return next((p.evaluations for p in self.observations
                     if p.best_energy <= target_energy + 1e-12), None)


def optimize_trace(
    costs: Sequence[float],
    method: str,
    *,
    angle_bits: int = 4,
    max_evaluations: int = 65,
    initial_angles: tuple[float, float] = (pi / 4, pi / 8),
    seed: int = 0,
) -> BenchmarkTrace:
    """Trace one of six methods under a common exact-energy evaluation cap.

    Sieve/grid/shuffled methods use the *same coordinate-wise optimizer*;
    only the candidate permutation differs. Random-joint samples angle pairs
    without replacement. Pattern is a derivative-free coordinate polling
    method that halves its step after unsuccessful polls and can stop early.
    Pattern trials remain on the same angle grid when starting on that grid.
    """
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    if angle_bits < 1 or max_evaluations < 1:
        raise ValueError("angle_bits and max_evaluations must be positive")
    if len(initial_angles) != 2 or not all(isfinite(x) for x in initial_angles):
        raise ValueError("initial_angles must be two finite angles")
    # Validate once, before computing costs or determining best possible cut.
    values = tuple(float(x) for x in costs)
    if len(values) < 2 or len(values) & (len(values) - 1) or not all(isfinite(x) for x in values):
        raise ValueError("costs must be finite and have length 2**n, n >= 1")

    grid_size = 1 << angle_bits
    grid_step = 2 * pi / grid_size
    rng = Random(seed)
    optimum = min(values)
    angles = [x % (2 * pi) for x in initial_angles]
    best_energy = float("inf")
    best_angles = tuple(angles)
    best_probability = 0.0
    points: list[Observation] = []

    def evaluate(gamma: float, beta: float) -> None:
        nonlocal best_energy, best_angles, best_probability
        gamma, beta = gamma % (2 * pi), beta % (2 * pi)
        probabilities = qaoa_probabilities(values, gamma, beta)
        energy = sum(v * p for v, p in zip(values, probabilities))
        if energy < best_energy - 1e-12:
            best_energy, best_angles = energy, (gamma, beta)
            best_probability = sum(p for v, p in zip(values, probabilities)
                                   if v == optimum)
        points.append(Observation(len(points) + 1, *best_angles,
                                  best_energy, best_probability))

    evaluate(*angles)  # The initial point costs one exact energy evaluation.
    if len(points) >= max_evaluations:
        return BenchmarkTrace(method, tuple(points))

    if method == "random_joint":
        # Search the same finite 2-D Cartesian grid, but without coordinate scans.
        pairs = [(gamma, beta) for gamma in range(grid_size)
                 for beta in range(grid_size)
                 if not (abs(angles[0] - gamma * grid_step) < 1e-12 and
                         abs(angles[1] - beta * grid_step) < 1e-12)]
        rng.shuffle(pairs)
        for gamma, beta in pairs:
            evaluate(gamma * grid_step, beta * grid_step)
            if len(points) >= max_evaluations:
                break
    elif method == "pattern":
        # Simple deterministic derivative-free poll of +/-step along both axes.
        # All tested points are on the grid for the default grid-aligned start.
        step = pi / 2
        while len(points) < max_evaluations and step >= grid_step - 1e-12:
            incumbent = best_angles
            before = best_energy
            for coordinate, sign in ((0, 1), (0, -1), (1, 1), (1, -1)):
                candidate = list(incumbent)
                candidate[coordinate] += sign * step
                evaluate(*candidate)
                if len(points) >= max_evaluations:
                    break
            if best_energy >= before - 1e-12:
                step /= 2
    else:
        # Coordinate-wise scans. The non-scanned coordinate is held fixed
        # throughout each scan, exactly as in optimize_with_recursive_sieve.
        while len(points) < max_evaluations:
            for coordinate in (0, 1):
                if method == "recursive":
                    order = list(recursive_keys(angle_bits))
                elif method == "original":
                    order = list(original_keys(angle_bits))
                else:
                    order = list(range(grid_size))
                    if method == "shuffled":
                        rng.shuffle(order)
                fixed = best_angles[1 - coordinate]
                for key in order:
                    candidate = list(best_angles)
                    candidate[coordinate] = key * grid_step
                    candidate[1 - coordinate] = fixed
                    evaluate(*candidate)
                    if len(points) >= max_evaluations:
                        break
                if len(points) >= max_evaluations:
                    break

    return BenchmarkTrace(method, tuple(points))


@dataclass(frozen=True)
class GraphCase:
    name: str
    n_qubits: int
    edges: tuple[tuple[int, int], ...]

    def costs(self) -> tuple[float, ...]:
        return maxcut_costs(self.n_qubits, self.edges)


CASES = (
    GraphCase("cycle4", 4, ((0, 1), (1, 2), (2, 3), (3, 0))),
    GraphCase("triangle3", 3, ((0, 1), (1, 2), (2, 0))),
    GraphCase("path5", 5, ((0, 1), (1, 2), (2, 3), (3, 4))),
    GraphCase("complete5", 5, tuple((i, j) for i in range(5)
                                     for j in range(i + 1, 5))),
    GraphCase("ladder6", 6, ((0, 1), (1, 2), (3, 4), (4, 5),
                             (0, 3), (1, 4), (2, 5))),
)


def grid_reference(costs: Sequence[float], angle_bits: int = 4) -> float:
    """An offline exhaustive 2-D grid reference, NOT a benchmarked solver.

    Its 2**(2*angle_bits) exact evaluations are excluded from each method's
    evaluation count. Do not mistake this reference for a free oracle.
    """
    if angle_bits < 1:
        raise ValueError("angle_bits must be positive")
    size = 1 << angle_bits
    return min(sum(v * p for v, p in zip(costs, qaoa_probabilities(
        costs, 2*pi*g/size, 2*pi*b/size)))
        for g in range(size) for b in range(size))


@dataclass(frozen=True)
class BenchmarkRun:
    case: str
    start: str
    method: str
    seed: int
    initial_energy: float
    grid_reference_energy: float
    target_energy: float
    used_evaluations: int
    first_hit: int | None
    energy_at_10: float
    energy_at_20: float
    energy_at_40: float
    energy_at_65: float
    optimal_probability_at_65: float


def run_suite(*, angle_bits: int = 4, budget: int = 65,
              random_seeds: int = 12, target_fraction: float = 0.8,
              cases: Sequence[GraphCase] = CASES,
              starts: Sequence[tuple[str, tuple[float, float]]] = (
                  ("default", (pi / 4, pi / 8)),
                  ("flat_beta", (pi / 8, pi / 4)),
                  ("shifted", (3 * pi / 8, 3 * pi / 8)),
              )) -> tuple[BenchmarkRun, ...]:
    """Compare all methods at identical evaluation caps, over several graphs.

    Targets are set *retrospectively* using offline exhaustive grid reference:
    initial - target_fraction * (initial - grid_ref). This is a convenient
    controlled experimental definition, not a deployable stopping rule without
    paying the reference computation cost.
    """
    if budget < 1 or random_seeds < 1:
        raise ValueError("budget and random_seeds must be positive")
    if not 0 < target_fraction < 1:
        raise ValueError("target_fraction must be in (0, 1)")
    if budget < 65:
        raise ValueError("budget must be at least 65 to report @65 checkpoints")
    rows = []
    for case in cases:
        costs = case.costs()
        reference = grid_reference(costs, angle_bits)
        for start, initial_angles in starts:
            initial = sum(v * p for v, p in zip(costs,
                qaoa_probabilities(costs, *initial_angles)))
            if initial - reference <= 1e-10:
                raise ValueError(f"case {case.name}, start {start}: no reference improvement")
            target = initial - target_fraction * (initial - reference)
            for method in METHODS:
                seeds = range(random_seeds) if method in ("shuffled", "random_joint") else range(1)
                for seed in seeds:
                    trace = optimize_trace(costs, method, angle_bits=angle_bits,
                        max_evaluations=budget, initial_angles=initial_angles, seed=seed)
                    rows.append(BenchmarkRun(case.name, start, method, seed, initial,
                        reference, target, trace.evaluations, trace.first_hit(target),
                        trace.at_budget(10).best_energy,
                        trace.at_budget(20).best_energy,
                        trace.at_budget(40).best_energy,
                        trace.at_budget(65).best_energy,
                        trace.at_budget(65).optimal_probability))

    return tuple(rows)
