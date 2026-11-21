# Variational Quantum Algorithms

A lightweight study project exploring variational quantum algorithms (VQAs), with room for IQM-compatible quantum software, CUDA experiments, and Lean proofs.

## Preprint

**Pauli Rikula**, *Coarse-to-Fine Dyadic Sampling: An Exact First-Hit Result and an Exploratory QAOA Benchmark*. [Zenodo record 24382960](https://zenodo.org/records/24382960) · [DOI 10.5281/zenodo.24382960](https://doi.org/10.5281/zenodo.24382960).

The preprint is a research note, not a peer-reviewed journal article. The [paper PDF](paper/dyadic_qaoa_note.pdf), [editable LaTeX source](paper/source/dyadic_qaoa_note.tex), and [reproducibility materials](paper/README.md) are available in this repository. No quantum hardware performance or quantum speedup is claimed.

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

## Hybrid angle optimizer and follow-up paper

The [hybrid optimizer](src/hybrid_qaoa.py) spends a configurable share of its energy budget on angle sampling and hands the best point to pattern search. It supports seven starting schedules, fixed splits, patience and a history-based checkpoint. The historical first-hit curves motivated a 13-call pilot out of 65. On a fresh 24-graph confirmation set, fixed Halton-13 reached 66/72 targets, fixed Halton-33 reached 72/72, and immediate polling reached 49/72. The shorter Halton pilot reached more targets by call 20. All first hits for Halton-33 occurred during the pilot.

Read the [follow-up research paper](paper/hybrid/hybrid_qaoa.pdf) or [use the optimizer and reproduce the comparison](paper/hybrid/README.md). This experiment uses one local continuation from the best pilot point. Multiple independent local restarts remain a separate research question.

## Search with fixed and variable-size valid clusters

The [cluster simulation and paper](paper/clusters/README.md) compare a single solid interval, multiple unequal blocks, guaranteed isolation, and uniformly selected subsets under explicit placement laws. The [variable-size results](paper/clusters/results/variable_summary.csv) separate binary hit/miss feedback from informative distance feedback. On 256 keys with a uniformly selected total of 8–32 and two to five randomly composed unequal blocks, the recursive sieve hit 599/600 targets by call 65. Switching after 13 hit 478/600 with binary feedback and 600/600 with distance feedback. The paper derives deadlines from the longest guaranteed block and checks matched reindexings of the earlier MaxCut energies.
