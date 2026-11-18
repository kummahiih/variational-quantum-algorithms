# Research journal

A concise record of work completed in this study repository. Update as experiments and proofs evolve.

## 2026-11-19 — Initial VQA workspace

- Created a deliberately minimal repository layout: flat `src/`, `examples/`, `notebooks/`, `tests/`, `docs/`, and a small Lean project under `lean/`.
- Added a Python project configuration and MIT license (copyright 2026 Pauli Rikula).
- Collected neighboring libraries and example implementations in [neighbors.md](neighbors.md), including IQM SDK/QAOA/VQE references and [pytorchqbit](https://github.com/kummahiih/pytorchqbit). The root `agents.txt` points to these references.

## Dyadic sieve search

**Motivation.** Search an entire `n`-bit key space for the first interesting key. If interesting keys occur in contiguous clusters, coarse-to-fine sampling may discover a cluster earlier than sequential enumeration. Unlike independent uniform random draws *with replacement*, the sieve never revisits a key.

**Python implementation.** [`src/dyadic_sieve.py`](../src/dyadic_sieve.py) enumerates odd multiples of decreasing powers of two, appending zero last. It yields integers via `keys(n_bits)` or most-significant-bit-first lists via `vectors(n_bits)`, suitable for conversion to PyTorch tensors. For four bits the sequence begins `1000, 0100, 1100, 0010, 0110, 1010, 1110`. It is iterative, not recursive.

**Python tests.** [`tests/test_dyadic_sieve.py`](../tests/test_dyadic_sieve.py) checks the four-bit ordering, uniqueness/completeness for bit widths 0 through 8, and negative-width rejection. The user reported all three tests passing.

**Lean formalization.** [`lean/DyadicSieve.lean`](../lean/DyadicSieve.lean) defines `sieveKey k i = (2*i+1)*2^k` and proves:
- Injectivity of odd multipliers and uniqueness of samples within a level.
- **Global uniqueness**: equal positive sieve keys imply equal level and index.
- Positivity of generated sieve keys; zero is handled separately in Python.
- A conditional cluster-hit lemma: a bounded forward-gap assumption implies every sufficiently wide interval contains a sample.
- A simple repeated-draw counterexample for sampling with replacement, plus the dyadic refinement identity.

The user reported `lake -d lean build` completing successfully with seven jobs. A subsequent commit removed an unused `simp` argument reported as a warning; that warning cleanup has not been separately verified.

**Important limits.** The Lean uniqueness theorem concerns the mathematical sampling formula; a full formal correspondence to the bounded Python generator (including completeness and exactly-once zero) has not yet been proved. The cluster lemma assumes bounded gaps rather than deriving the bound from the sieve. There is no formal probabilistic expected-trial comparison or universal optimality theorem. Random sampling *without* replacement also avoids duplicates.

## Next questions

- Prove the actual finite-prefix gap bound for the dyadic ordering and a worst-case discovery bound for contiguous clusters.
- Prove that the bounded `n`-bit generator enumerates all `2^n` keys exactly once.
- Specify a probability model for cluster location/width and compare expected first-hit times with random sampling with and without replacement.
- Explore interoperability with `pytorchqbit` and IQM VQA examples when concrete experiments are selected.

## Verification commands

From the repository root:

```bash
python -m unittest discover -s tests -v
lake -d lean build
```
