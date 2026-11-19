# Variational Quantum Algorithms

A lightweight study project exploring variational quantum algorithms (VQAs), with room for IQM-compatible quantum software, CUDA experiments, and Lean proofs.

## Layout

- `docs/` — notes and mathematical background
- `lean/` — small Lean 4 proofs
- `src/` — implementation code (flat for now)
- `examples/` — runnable examples
- `notebooks/` — exploratory notebooks
- `tests/` — tests

The structure is intentionally provisional. Dependencies, IQM integration, and CUDA integration will be chosen after refining the research ideas.

## Dyadic sampling algorithms

Two dependency-free implementations explore an entire `n`-bit key space,
coarse to fine, without repeated keys:

- [`src/dyadic_sieve.py`](src/dyadic_sieve.py) — original algorithm; ascending numeric order within each refinement level.
- [`src/recursive_dyadic_sieve.py`](src/recursive_dyadic_sieve.py) — recursively ordered levels using bit reversal (finite base-2 van der Corput order, with zero last).

Both provide `keys(n_bits)` and `vectors(n_bits)`. For example:

```python
from dyadic_sieve import keys as original_keys
from recursive_dyadic_sieve import keys as recursive_keys

print(list(original_keys(4)))
# [8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15, 0]
print(list(recursive_keys(4)))
# [8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0]
```

Run from `src/` or add it to your Python import path. See
[`docs/journal.md`](docs/journal.md) for the power-of-two solid-cluster
finding-time proof. The new variant has not been formalized separately in Lean.
