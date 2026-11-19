# Handover for the next conversation

**Repository:** [kummahiih/variational-quantum-algorithms](https://github.com/kummahiih/variational-quantum-algorithms)  
**Last updated:** 2026-11-19  
**State:** Paused after building a first, dependency-free QAOA simulation tuned with the recursive dyadic sieve. No new implementation or proof work is requested until the owner resumes.

## Prompt to paste into a new conversation

```text
Continue my GitHub project kummahiih/variational-quantum-algorithms.

Please use the connected GitHub repository as the source of truth.
Read AGENTS.md, README.md, docs/journal.md, docs/neighbors.md and
docs/handover.md before proposing or changing anything. Keep the Python
src/ layout flat and the Lean project minimal.

We have two distinct coarse-to-fine n-bit sampling algorithms:
  src/dyadic_sieve.py             ascending order inside dyadic levels
  src/recursive_dyadic_sieve.py   bit-reversed order inside each level
Both enumerate every n-bit key exactly once, with zero last.

We proved an exact first-hit sum for uniformly positioned contiguous
power-of-two clusters (m >= 2) in the original dyadic sieve. My Lean
build succeeded with 19 jobs. We are stopping additional Lean work
for now; do not add new proofs unless I explicitly ask.

We also implemented a small one-layer QAOA statevector simulator in
src/sieve_qaoa.py. The recursive sieve chooses discretized free
circuit angles gamma and beta, using coordinate scans, optional early
energy threshold and evaluation budget. It does not run on quantum
hardware and is not Grover search. There is a 4-vertex MaxCut example
in examples/sieve_qaoa_maxcut.py and tests/test_sieve_qaoa.py.

The next useful experiment, when I request it, is to compare recursive
sieve, original sieve, and conventional parameter optimizers at equal
objective-evaluation/shot budgets, especially time to reach an energy
threshold. A complete scan of the same angle grid makes sieve order
irrelevant to the final minimum; ordering matters mainly with
early stopping or limited budgets. Do not claim a quantum speedup.

For now, first summarize the repository's current state concisely,
and let me choose what to do next. Do not automatically start a
benchmark or rewrite the algorithms.
```

## Source map

| File | Role |
| --- | --- |
| [`AGENTS.md`](../AGENTS.md) | Conventions: flat `src/`, minimal Lean, GitHub Markdown math fences |
| [`README.md`](../README.md) | Project overview, example invocation |
| [`docs/journal.md`](journal.md) | Chronological research record, proof status, QAOA simulation |
| [`docs/neighbors.md`](neighbors.md) | IQM/PyTorch neighbors, QMC sequences, Grover/QAOA/VQA literature |
| [`src/dyadic_sieve.py`](../src/dyadic_sieve.py) | Original ascending-within-level sieve |
| [`src/recursive_dyadic_sieve.py`](../src/recursive_dyadic_sieve.py) | Recursive bit-reversal (finite base-2 van der Corput) sieve |
| [`src/cluster_expectation.py`](../src/cluster_expectation.py) | Exact finite cluster-first-hit calculations |
| [`src/sieve_qaoa.py`](../src/sieve_qaoa.py) | One-layer QAOA, exact statevector simulator, angle optimizer |
| [`examples/sieve_qaoa_maxcut.py`](../examples/sieve_qaoa_maxcut.py) | Four-vertex MaxCut demonstration |
| [`tests/test_sieve_qaoa.py`](../tests/test_sieve_qaoa.py) | QAOA tests, including early stopping and budget |
| [`lean/FirstHitSum.lean`](../lean/FirstHitSum.lean) | Final end-to-end integer first-hit sum theorem, original sieve only |

## What is established

**Two sieve orders.** For four bits:

- Original: `8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15, 0`.
- Recursive: `8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0`.

Both have the same complete dyadic refinement levels. Their within-level ordering differs, which can affect how quickly they find *non-solid* hit sets.

**Proved mathematical result.** For `N = 2^n`, `m = 2^r`, `2 <= m <= N`, and a solid cluster of `m` successful consecutive integer-ordered keys whose start is uniform over all `N-m+1` possibilities:

```math
\mathbb{E}[T] = \frac{N(N-m+2)}{2m(N-m+1)}.
```

The exact **integer sum identity** for the original sieve is machine-checked in Lean; the expectation is obtained mathematically by dividing by the number of possible starts. The user reported `lake -d lean build` **successful (19 jobs)** on Lean 4.36.0. The same expectation for the recursive variant has been checked in Python, **not separately proved in Lean**. The singleton `m=1` and arbitrary non-power-of-two lengths are not included in the final formal theorem.

**QAOA draft.** `src/sieve_qaoa.py` creates the state

```math
|\psi(\gamma,\beta)\rangle
= e^{-i\beta\sum_j X_j} e^{-i\gamma H_C}|+\rangle^{\otimes n}
```

for a binary-vector cost `f(x)`. The optimizer uses `recursive_dyadic_sieve.keys(angle_bits)` to choose `2*pi*k/2**angle_bits` candidates for `gamma`, then `beta`, repeating for `sweeps`. Options include `target_energy` and `max_evaluations`, which counts exact statevector energy evaluations. This is a **classical ideal simulation** whose dense cost table and statevector scale as `2**n`.

In the documented four-vertex cycle MaxCut example (`angle_bits=4`, `sweeps=2`), the previous session reported expected energy improving from `-1.0` to `-3.0` after **65 exact statevector evaluations**; the optimal cut bitstrings `0101` and `1010` together have about **53% output probability**. Seven dedicated QAOA tests were reported passing in the previous session; the repository owner has not yet provided independent test/build output for this newest Python draft.

## When resuming

From the repository root:

```bash
git pull
python examples/sieve_qaoa_maxcut.py
python -m unittest discover -s tests -v
lake -d lean build
```

Python requires **3.11+**, with no third-party runtime dependencies for the current draft. The Lean build is optional when only changing Python. Follow the repository's `AGENTS.md` conventions.

A fair subsequent comparison should measure **time-to-target**, best energy at matched **evaluation budgets**, and probability of measuring a satisfactory binary solution. Compare ascending sieve, recursive sieve, ordinary grid, random and (if dependencies are acceptable) Sobol/Halton or an optimizer such as Rotosolve. Keep noise and actual shot costs distinct from ideal statevector evaluations; make no inference of universal VQA or quantum advantage from the contiguous-cluster theorem. QAOA searches circuit angles while its output distribution samples binary solutions; Grover searches marked states with a coherent oracle and is not the same operation.
