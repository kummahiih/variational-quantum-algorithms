# Handover for the next conversation

**Repository:** [kummahiih/variational-quantum-algorithms](https://github.com/kummahiih/variational-quantum-algorithms) (public)  
**Last updated:** 2026-11-21

**Preprint:** [Zenodo record 24382960](https://zenodo.org/records/24382960) (record URL supplied by Pauli Rikula)  
**State:** The original preprint and formal result are followed by a [separate hybrid optimizer study](../paper/hybrid/README.md). The new implementation combines seven pilot schedules with one local pattern search from the best sampled point. Fixed, patience and learned handoffs are benchmarked. Multiple local restarts remain a distinct proposal. The [target-geometry follow-up](../paper/clusters/README.md) tests the actual solid-run assumption, multiple variable-size blocks, isolated and unrestricted random targets, and matched reindexings of the earlier QAOA grids. Sections 5–6 of the new paper cover unequal block sizes.

## Copy-ready prompt for the next session

~~~text
Continue my GitHub project:
https://github.com/kummahiih/variational-quantum-algorithms

Use the connected repository's main branch as the source of truth.
First read AGENTS.md, README.md, docs/handover.md, docs/journal.md,
docs/qaoa_benchmark.md, docs/neighbors.md, and paper/README.md.
Keep src/ flat and the Lean project minimal. Do not add Lean proofs
unless I explicitly request them.

The repository is public. The author is Pauli Rikula (no affiliation).
The preprint URL I provided is https://zenodo.org/records/24382960.
The paper PDF is paper/dyadic_qaoa_note.pdf, and editable LaTeX,
benchmark CSVs and reproduction scripts are under paper/.
The final paper section declares generative AI assistance.

I ran lake -d lean build successfully (19 jobs) and
python -m unittest discover -s tests -v (29 tests passed).
These are independent owner-reported checks.

We implemented an original coarse-to-fine dyadic sieve and a
recursive/bit-reversed dyadic sieve. The Lean theorem establishes
the original sieve's integer first-hit sum for uniformly placed
contiguous power-of-two hit clusters, under its assumptions.
The corresponding expectation follows mathematically, but the
recursive variant was not separately proven in Lean.

The dependency-free exact classical p=1 QAOA statevector simulation
uses recursive sieve ordering to scan circuit angles gamma/beta.
The benchmark compares six optimization methods on five tiny
MaxCut graphs x three starts, with 420 recorded method runs.
Recursive and original sieve target-hit rates tie in aggregate.
The simple derivative-free pattern-search baseline performs better
in some settings; this is not a quantum hardware or speedup claim.

Read paper/hybrid/README.md and the new research draft for the
second study. Its source is src/hybrid_qaoa.py. On fresh cohort B,
fixed Halton pilots of 13 and 33 calls hit 66/72 and 72/72 targets.
The 13-call pilot led at call 20. The 33-call pilot and uninterrupted
Halton hit all targets before any local refinement at call 34.
Adaptive patience and the learned checkpoint underperformed Halton-13.
The original published manuscript remains the record of the first study.
Multiple local restarts would be a separate experiment.

The third study is paper/clusters/cluster_assumption.pdf. Its generator
is examples/benchmark_cluster_assumption.py; --variable-only runs the
variable-width and unequal-block cases. Distinguish a uniformly placed
block, a uniform isolated subset and an unrestricted uniform subset.
State the placement law, the feedback model, and the budget with rates.
For at most r runs with total m, at least one run has length ceil(m/r).
The 65-call results for random unequal blocks on 256 keys were 599/600
for pure recursive sampling and 478/600 for a 13-call hybrid with
membership feedback. Exact distance feedback gave the hybrid 600/600.

First give a concise state summary, then let me choose next steps.
~~~

## Source map

| File | Role |
| --- | --- |
| [`AGENTS.md`](../AGENTS.md) | Conventions: flat `src/`, minimal Lean, GitHub Markdown math |
| [`README.md`](../README.md) | Project overview, Zenodo preprint, verification |
| [`docs/journal.md`](journal.md) | Chronological record, including benchmark and publication update |
| [`docs/qaoa_benchmark.md`](qaoa_benchmark.md) | Experiment protocol, six methods, limitations and results |
| [`docs/neighbors.md`](neighbors.md) | IQM/PyTorch neighbors, QMC sequences, Grover/VQA and pattern-search prior art |
| [`docs/working_model.md`](working_model.md) | Technical intuition and derivations |
| [`src/dyadic_sieve.py`](../src/dyadic_sieve.py) | Original ascending-within-level sieve |
| [`src/recursive_dyadic_sieve.py`](../src/recursive_dyadic_sieve.py) | Recursive bit-reversal (finite base-2 van der Corput with zero last) sieve |
| [`src/cluster_expectation.py`](../src/cluster_expectation.py) | Finite cluster first-hit calculations |
| [`lean/FirstHitSum.lean`](../lean/FirstHitSum.lean) | Machine-checked original-sieve **integer sum** |
| [`src/sieve_qaoa.py`](../src/sieve_qaoa.py) | p=1 QAOA exact statevector simulator and sieve angle optimizer |
| [`src/qaoa_benchmark.py`](../src/qaoa_benchmark.py) | Six benchmark methods; exact evaluation accounting |
| [`examples/sieve_qaoa_maxcut.py`](../examples/sieve_qaoa_maxcut.py) | Four-cycle MaxCut sanity check |
| [`examples/benchmark_qaoa_optimizers.py`](../examples/benchmark_qaoa_optimizers.py) | Benchmark runner |
| [`tests/test_qaoa_benchmark.py`](../tests/test_qaoa_benchmark.py) | Eight benchmark-specific tests, included in 29-test suite |
| [`paper/dyadic_qaoa_note.pdf`](../paper/dyadic_qaoa_note.pdf) | Five-page research note by Pauli Rikula |
| [`paper/source/dyadic_qaoa_note.tex`](../paper/source/dyadic_qaoa_note.tex) | Editable paper and final AI declaration |
| [`paper/results/qaoa_benchmark_raw.csv`](../paper/results/qaoa_benchmark_raw.csv) | 420 experimental records |
| [`paper/results/qaoa_benchmark_summary.csv`](../paper/results/qaoa_benchmark_summary.csv) | Aggregate results |
| [`paper/source/plot_results.py`](../paper/source/plot_results.py) | Regenerates figures from results |
| [`paper/source/verify_math.py`](../paper/source/verify_math.py) | Finite enumerations/energy checks (not Lean proofs) |
| [`paper/README.md`](../paper/README.md) | Reproduction and LaTeX build instructions |

## What is established, with limits

**Dyadic sequences.** Both orderings visit each of the `N=2**n` keys exactly once and have identical complete dyadic refinement *sets* but different *within-level ordering*. For four bits:

- Original: `8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15, 0`.
- Recursive: `8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0`.

**Formalization.** For `N=2**n`, `m=2**r`, `2 <= m <= N`, and a contiguous block of `m` successful integer-ordered keys whose start is uniform among the `N-m+1` possible starts:

~~~math
\mathbb{E}[T] = \frac{N(N-m+2)}{2m(N-m+1)}.
~~~

The Lean theorem formalizes the **integer first-hit sum identity for the original sieve**. Dividing by the number of starts yields the displayed expectation as a mathematical corollary. Equality for the recursive sieve on this cluster model was numerically checked, **not separately formalized in Lean**. The theorem does not cover arbitrary target geometry or a quantum algorithm.

**QAOA simulator.** `src/sieve_qaoa.py` implements the exact noiseless classical statevector

~~~math
|\psi(\gamma,\beta)\rangle =
e^{-i\beta\sum_j X_j}e^{-i\gamma H_C}|+\rangle^{\otimes n}.
~~~

The optimizer uses sieve-selected angles on a finite grid, alternately scanning gamma and beta. It supports `target_energy` and `max_evaluations`. Every counted evaluation is an **exact classical statevector objective evaluation**, not a physical measurement shot. Cost/statevector arrays scale as `2**n`. On the four-cycle MaxCut example, expected negative-cut energy improves from `-1` to `-3` after 65 evaluations, with total probability around 53.125% on the two maximum-cut bitstrings.

**Optimizer benchmark.** See [full design and limitations](qaoa_benchmark.md). Five small MaxCut graphs, three initial angle pairs, 16 grid angles per coordinate, and 65 counted evaluations *including initial evaluation*, with 12 seeds for each randomized method. Total: **420 rows**; deterministic methods have 15 runs each, randomized methods 180 each. Methods: recursive sieve, original sieve, ascending grid, shuffled coordinate scan, random joint pairs, and simple pattern-search-style polling.

| Method | Target hit by 10 | By 20 | By 65 |
| --- | ---: | ---: | ---: |
| Recursive sieve | 60.0% | 66.7% | 86.7% |
| Original sieve | 60.0% | 66.7% | 86.7% |
| Random joint pairs | 52.8% | 71.1% | 95.6% |
| Pattern-search polling | 40.0% | 100% | 100% |

The grid reference for retrospective thresholds is an **offline exhaustive 16x16 reference (256 extra objective evaluations per graph) not charged to individual method budgets**. Results from a few noiseless small problems do not show universal superiority or quantum speedup. Recursive and original sieve curves **coincide exactly in the aggregate plot**; the paper intentionally renders their coincident traces visibly.

**Literature and possible next experiment.** The pattern-search baseline is classical local polling. Halton/sobol-style low-discrepancy initialization plus conventional optimization is established prior art; [neighbors.md](neighbors.md) now cites a concrete Halton + global pattern search application, classical multistart work, and related direct-search papers. A *recursive-dyadic multistart pattern-search* hybrid is still **only a research proposal**. A meaningful study must choose a genuine multidimensional starting-point schedule, count all global and local objective evaluations fairly, compare alternative starts under the same local search, and account for periodic angle wrapping and repeated evaluations. Do not claim novelty or a performance advantage without literature review and evidence.

## Verification and how to resume

**Author-reported, successful (20 November 2026):** `lake -d lean build` completed with **19 jobs**; `python -m unittest discover -s tests -v` passed **29 tests** in **0.409 seconds**. Preparation-environment checks also reproduced the 420-row CSV and independently checked finite first-hit calculations and analytic four-cycle QAOA energy, but do not replace formalization or full hardware tests.

From repo root (Python 3.11+; core simulator/benchmark needs no third-party runtime dependency):

~~~bash
git pull
python -m unittest discover -s tests -v
lake -d lean build
python examples/sieve_qaoa_maxcut.py
python examples/benchmark_qaoa_optimizers.py --csv paper/results/reproduced.csv
python paper/source/verify_math.py
~~~

For the figure and PDF build, see [paper/README.md](../paper/README.md); plotting needs matplotlib and the paper needs LaTeX. Do not overwrite the tracked PDF without intentionally updating its source and rerunning the build.

**Research scope:** Keep circuit-angle optimization separate from Grover-like marked-bitstring search; distinguish the original Lean theorem from the recursive variant's numerical checks; distinguish offline grid-reference target construction from realistic online stopping; distinguish ideal statevector energy evaluations from circuit counts/shots. The 21 November follow-up implements a single local continuation. See the [hybrid study and reproduction guide](../paper/hybrid/README.md) for its code, data and separate manuscript.
