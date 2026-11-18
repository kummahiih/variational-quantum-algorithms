"""Exact first-hit expectations for a uniformly located solid cluster.

The cluster is an interval [start, start + length) in [0, 2**n_bits).
All N-length+1 starts are equally likely. Sampling order is the
nonrecursive dyadic sieve, without replacement.

The exact expectation is a Fraction. This is not a Monte Carlo estimate.
"""

from fractions import Fraction

try:
    from .dyadic_sieve import keys
except ImportError:  # Direct script execution from src/
    from dyadic_sieve import keys


def first_hit_times(n_bits: int, length: int) -> list[int]:
    """1-based first hit for every possible contiguous cluster start."""
    if n_bits < 0:
        raise ValueError("n_bits must be nonnegative")
    size = 1 << n_bits
    if not 1 <= length <= size:
        raise ValueError("length must be between 1 and 2**n_bits")
    first = [0] * (size - length + 1)
    remaining = len(first)
    for trial, key in enumerate(keys(n_bits), start=1):
        # The key belongs to clusters starting in [key-length+1, key].
        for start in range(max(0, key - length + 1), min(key, size - length) + 1):
            if first[start] == 0:
                first[start] = trial
                remaining -= 1
        if remaining == 0:
            break
    return first


def expected_first_hit(n_bits: int, length: int) -> Fraction:
    """Exact average over uniformly distributed cluster locations."""
    times = first_hit_times(n_bits, length)
    return Fraction(sum(times), len(times))


def random_with_replacement_expectation(n_bits: int, length: int) -> Fraction:
    """Independent uniform draws, including possible repeated keys."""
    if n_bits < 0:
        raise ValueError("n_bits must be nonnegative")
    size = 1 << n_bits
    if not 1 <= length <= size:
        raise ValueError("length must be between 1 and 2**n_bits")
    return Fraction(size, length)


def random_without_replacement_expectation(n_bits: int, length: int) -> Fraction:
    """Uniformly random permutation of the key space."""
    if n_bits < 0:
        raise ValueError("n_bits must be nonnegative")
    size = 1 << n_bits
    if not 1 <= length <= size:
        raise ValueError("length must be between 1 and 2**n_bits")
    return Fraction(size + 1, length + 1)


if __name__ == "__main__":
    for length in (1, 2, 3, 4, 8, 16):
        print(
            f"N=16 m={length}: sieve={expected_first_hit(4, length)}, "
            f"random replacement={random_with_replacement_expectation(4, length)}, "
            f"random permutation={random_without_replacement_expectation(4, length)}"
        )
