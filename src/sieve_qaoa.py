"""One-layer QAOA for a binary objective, tuned by the recursive dyadic sieve.

This deliberately small, dependency-free statevector demo separates two spaces:
* Binary solution states x (the n qubits and the diagonal cost H_C).
* Continuous circuit angles gamma and beta, which the recursive sieve scans.

It exactly simulates quantum amplitudes rather than executing real hardware.
The search is derivative-free coordinate optimization over a finite angle grid;
it is not Grover search and makes no general speedup claim.
"""

from dataclasses import dataclass
from cmath import exp
from math import cos, isfinite, pi, sin, sqrt
from collections.abc import Sequence

from recursive_dyadic_sieve import keys as recursive_keys


def _validate_costs(costs: Sequence[float]) -> tuple[float, ...]:
    values = tuple(float(cost) for cost in costs)
    size = len(values)
    if size < 2 or size & (size - 1):
        raise ValueError("costs must have length 2**n for n >= 1")
    if not all(isfinite(value) for value in values):
        raise ValueError("costs must contain finite real values")
    return values


def maxcut_costs(n_qubits: int, edges: Sequence[tuple[int, int]]) -> tuple[float, ...]:
    """Return f(x) = -number of cut edges for an n-qubit MaxCut instance.

    Each integer x represents a binary solution assignment. Minimizing f
    corresponds to maximizing the cut size. Duplicate edges count twice.
    """
    if n_qubits < 1:
        raise ValueError("n_qubits must be positive")
    for left, right in edges:
        if not (0 <= left < n_qubits and 0 <= right < n_qubits) or left == right:
            raise ValueError("each edge must join two distinct valid vertices")
    return tuple(
        float(-sum(((x >> left) ^ (x >> right)) & 1 for left, right in edges))
        for x in range(1 << n_qubits)
    )


def _probabilities(values: tuple[float, ...], gamma: float, beta: float) -> tuple[float, ...]:
    """QAOA(gamma,beta) = U_X(beta) U_C(gamma) |+>^n, p=1."""
    size = len(values)
    norm = 1 / sqrt(size)
    state = [exp(-1j * gamma * cost) * norm for cost in values]

    # Mixer: exp(-i beta X) on each qubit, applied to basis-state pairs.
    c, s = cos(beta), -1j * sin(beta)
    for qubit in range(size.bit_length() - 1):
        mask = 1 << qubit
        for zero in range(size):
            if zero & mask:
                continue
            one = zero | mask
            a, b = state[zero], state[one]
            state[zero] = c * a + s * b
            state[one] = s * a + c * b
    return tuple(abs(amplitude) ** 2 for amplitude in state)


def qaoa_probabilities(costs: Sequence[float], gamma: float, beta: float) -> tuple[float, ...]:
    """Exact output probabilities for all bitstrings in a one-layer QAOA."""
    return _probabilities(_validate_costs(costs), gamma, beta)


def qaoa_energy(costs: Sequence[float], gamma: float, beta: float) -> float:
    """Exact expected diagonal energy E(gamma,beta), to be minimized."""
    values = _validate_costs(costs)
    return sum(cost * probability for cost, probability in
               zip(values, _probabilities(values, gamma, beta)))


@dataclass(frozen=True)
class SieveQAOAResult:
    gamma: float
    beta: float
    expected_energy: float
    evaluations: int
    probabilities: tuple[float, ...]

    @property
    def most_likely_bitstring(self) -> str:
        n_qubits = (len(self.probabilities) - 1).bit_length()
        index = max(range(len(self.probabilities)), key=self.probabilities.__getitem__)
        return format(index, f"0{n_qubits}b")


def optimize_with_recursive_sieve(
    costs: Sequence[float],
    *,
    angle_bits: int = 4,
    sweeps: int = 2,
    initial_angles: tuple[float, float] = (pi / 4, pi / 8),
    target_energy: float | None = None,
) -> SieveQAOAResult:
    """Tune QAOA's two free angles by repeated coordinate-wise sieve scans.

    On each coordinate, try angles 2*pi*k / 2**angle_bits in the order
    given by recursive_dyadic_sieve.keys(angle_bits). Retain the best angle
    with the other coordinate fixed. Return early if target_energy is met.

    The starting angles are deliberately nonzero: if gamma=0 or beta=0,
    the one-layer QAOA energy can be flat when varying the other angle.

    Each evaluation is one *exact statevector simulation*, NOT one shot or
    one quantum-hardware call. The optimization explores angles, not binary
    solution vectors; it is a classical outer loop around a quantum circuit.
    """
    values = _validate_costs(costs)
    if angle_bits < 1:
        raise ValueError("angle_bits must be positive")
    if sweeps < 1:
        raise ValueError("sweeps must be positive")
    if len(initial_angles) != 2 or not all(isfinite(angle) for angle in initial_angles):
        raise ValueError("initial_angles must be two finite angles")
    if target_energy is not None and not isfinite(target_energy):
        raise ValueError("target_energy must be finite")

    angles = list(initial_angles)
    grid_size = 1 << angle_bits
    energy = sum(cost * p for cost, p in
                 zip(values, _probabilities(values, *angles)))
    evaluations = 1

    def finish() -> SieveQAOAResult:
        return SieveQAOAResult(
            gamma=angles[0], beta=angles[1], expected_energy=energy,
            evaluations=evaluations,
            probabilities=_probabilities(values, *angles),
        )

    if target_energy is not None and energy <= target_energy:
        return finish()

    for _ in range(sweeps):
        for coordinate in (0, 1):
            best_angle = angles[coordinate]
            best_energy = energy
            for key in recursive_keys(angle_bits):
                candidate = (2 * pi * key) / grid_size
                trial_angles = angles.copy()
                trial_angles[coordinate] = candidate
                trial_energy = sum(cost * p for cost, p in
                                   zip(values, _probabilities(values, *trial_angles)))
                evaluations += 1
                if trial_energy < best_energy - 1e-12:
                    best_angle, best_energy = candidate, trial_energy
                if target_energy is not None and best_energy <= target_energy:
                    angles[coordinate] = best_angle
                    energy = best_energy
                    return finish()
            angles[coordinate] = best_angle
            energy = best_energy
    return finish()
