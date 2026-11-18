"""Coarse-to-fine sampling of an n-bit key space.

Yields integer keys in dyadic midpoint order, followed by binary vectors.
For 4 bits: 1000, 0100, 1100, 0010, 0110, 1010, 1110, ...
No recursion or dependencies. Stop as soon as an interesting key is found.
"""

from collections.abc import Iterator


def keys(n_bits: int) -> Iterator[int]:
    """Yield each key from 1 to 2**n_bits-1 once, coarse to fine.

    Zero is yielded last, so the entire key space is covered.
    """
    if n_bits < 0:
        raise ValueError("n_bits must be nonnegative")
    for level in range(n_bits):
        step = 1 << (n_bits - level - 1)
        for key in range(step, 1 << n_bits, step << 1):
            yield key
    yield 0


def vectors(n_bits: int) -> Iterator[list[int]]:
    """Yield MSB-first binary vectors, e.g. [1, 0, 1, 0].

    Feed a vector to torch.tensor(vector, dtype=...) if PyTorch is desired.
    """
    for key in keys(n_bits):
        yield [(key >> bit) & 1 for bit in range(n_bits - 1, -1, -1)]


if __name__ == "__main__":
    for vector in vectors(4):
        print(vector)
