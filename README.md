# Variational Quantum Algorithms

A lightweight study project exploring variational quantum algorithms (VQAs), with room for IQM-compatible quantum software, CUDA experiments, and Lean proofs.

## Preprint

**Pauli Rikula**, *Coarse-to-Fine Dyadic Sampling: An Exact First-Hit Result and an Exploratory QAOA Benchmark*. [Zenodo record 24382960](https://zenodo.org/records/24382960) · [DOI 10.5281/zenodo.24382960](https://doi.org/10.5281/zenodo.24382960).

The preprint is a research note, not a peer-reviewed journal article. The [paper PDF](paper/dyadic_qaoa_note.pdf), [editable LaTeX source](paper/source/dyadic_qaoa_note.tex), and [reproducibility materials](paper/README.md) are available in this repository. No quantum hardware performance or quantum speedup is claimed.

## Does a recursive sieve help initialize QAOA pattern search?

The two follow-up papers test this question on the same 24 MaxCut graphs and three starting points per graph. Both hybrids spend 13 evaluations on their chosen start and run the same local pattern search with up to 52 calls left. A valid key meets the energy threshold. A solid block consists of consecutive valid keys in the sieve's indexing.

| Target placement | Recursive sieve + pattern | Halton + pattern | Immediate pattern |
| --- | ---: | ---: | ---: |
| Native QAOA grids, all valid keys isolated (72 cases) | 65.3% | 91.7% | 68.1% |
| Same energies, one uniformly placed solid block (32 placements per case) | 79.0% | 73.8% | 48.3% |

The figures are target-hit rates by 65 evaluations. The planted comparison reindexes exact simulated energies and preserves the starting energy, target count and threshold. The [nonclustered baseline paper](paper/hybrid/hybrid_qaoa.pdf) describes the optimizer and the switch timing. The [matched comparison paper](paper/clusters/cluster_assumption.pdf) shows the starter comparison on page 1 and the handoff counts for variable-size blocks on page 6. See the [optimizer](src/hybrid_qaoa.py) and [reproducible simulation](paper/clusters/README.md).

The [16-call handoff paper](paper/handoff/paired_handoff.pdf) compares recursive and random-order starts followed by identical pattern search on matched QAOA-derived energies. With one solid target block, the recursive hybrid hit 88.6% by call 65 and the random-start hybrid hit 73.1%. On strictly isolated targets the rates were 77.5% and 81.6%. Separate calibration selected 20 calls, the longest pilot tested. See the [study protocol and data](paper/handoff/README.md).

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

## One-layer QAOA with recursive-sieve parameter tuning

[`src/sieve_qaoa.py`](src/sieve_qaoa.py) implements a small, **one-layer QAOA**
for a binary-vector cost function. It prepares a uniform superposition,
applies the diagonal cost unitary `exp(-i gamma H_C)`, then the mixing
unitary `exp(-i beta sum X)`, and minimizes the resulting expected cost.
The **recursive dyadic sieve searches the circuit angles** `gamma` and
`beta` on a finite grid by alternating one-angle scans; it does **not**
directly search the binary solution vectors.

Run the four-vertex MaxCut example:

```bash
python examples/sieve_qaoa_maxcut.py
python -m unittest discover -s tests -v
```

The example's ideal statevector run reduces the expected negative cut size
from `-1` to `-3` with `65` exact energy evaluations. It reports the
most likely measured bitstrings and their probabilities.

The optimizer accepts `angle_bits`, `sweeps`, `target_energy`, and
`max_evaluations`. **Order matters under early stopping or a finite
evaluation budget**; complete scans visit the same angle grid irrespective
of permutation. This is a small **classical exact-statevector simulation**,
not a quantum-hardware implementation or evidence of quantum speedup.
The diagonal cost list has `2**n` entries, so the simulator is not
scalable to large `n`. See [`docs/journal.md`](docs/journal.md).

## Benchmarks, verification and next questions

The [optimizer benchmark](docs/qaoa_benchmark.md) compares recursive and original dyadic ordering against ascending/shuffled coordinate scans, random joint-angle sampling, and a simple derivative-free pattern search. It uses five small MaxCut graphs, three starting points, and up to 65 **exact statevector energy evaluations** per run. [Raw data and scripts](paper/README.md) document 420 runs. In this preliminary comparison, the two sieve orders tie in aggregate; pattern search reaches the defined target more reliably by 20 evaluations. These are limited, noiseless experiments, not universal performance claims.

**Owner-reported verification (20 November 2026):** `lake -d lean build` succeeded (**19 jobs**) and `python -m unittest discover -s tests -v` passed (**29 tests**). The Lean proof formalizes the original sieve's integer first-hit sum under its stated assumptions; it does not prove a QAOA optimization advantage.

```bash
python examples/benchmark_qaoa_optimizers.py
python -m unittest discover -s tests -v
lake -d lean build
```
