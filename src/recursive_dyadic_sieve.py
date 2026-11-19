"""Dyadic sieve with bit-reversal ordering inside each refinement level.

This is the finite base-2 van der Corput order (with zero last).
Like the original dyadic sieve, it visits coarse levels before fine ones,
but it visits the candidates within each level recursively rather than
in ascending numerical order.

For four bits: 8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0.
"""

from collections.abc import Iterator


def _reverse_bits(index: int, width: int) -> int:
    """Reverse exactly ``width`` low-order bits; width zero gives zero."""
    result = 0
    for _ in range(width):
        result = (result << 1) | (index & 1)
        index >>= 1
    return result


def keys(n_bits: int) -> Iterator[int]:
    """Yield each n-bit key once, in recursively ordered dyadic levels.

    Values at level ``level`` are odd multiples of ``2**(n_bits-level-1)``.
    Their odd multipliers are indexed by the bit-reversal permutation
    of ``range(2**level)``. Zero is yielded last.
    """
    if n_bits < 0:
        raise ValueError("n_bits must be nonnegative")

    for level in range(n_bits):
        step = 1 << (n_bits - level - 1)
        for index in range(1 << level):
            reversed_index = _reverse_bits(index, level)
            yield (2 * reversed_index + 1) * step
    yield 0


def vectors(n_bits: int) -> Iterator[list[int]]:
    """Yield MSB-first binary vectors in the same order as ``keys``."""
    for key in keys(n_bits):
        yield [(key >> bit) & 1 for bit in range(n_bits - 1, -1, -1)]


if __name__ == "__main__":
    for vector in vectors(4):
        print(vector)
