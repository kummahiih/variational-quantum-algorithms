# Research journal

A concise record of work completed in this study repository. Update as experiments and proofs evolve.

## 2026-11-19 — Initial VQA workspace

- Created a deliberately minimal repository layout: flat `src/`, `examples/`, `notebooks/`, `tests/`, `docs/`, and a small Lean project under `lean/`.
- Added a Python project configuration and MIT license (copyright 2026 Pauli Rikula).
- Collected neighboring libraries and example implementations in [neighbors.md](neighbors.md), including IQM SDK/QAOA/VQE references and [pytorchqbit](https://github.com/kummahiih/pytorchqbit). The root [`AGENTS.md`](../AGENTS.md) points to these references and records repository conventions.

## Dyadic sieve search

**Motivation.** Search an entire `n`-bit key space for the first interesting key. If interesting keys occur in contiguous clusters, coarse-to-fine sampling may discover a cluster earlier than sequential enumeration. Unlike independent uniform random draws *with replacement*, the sieve never revisits a key.

**Python implementation.** [`src/dyadic_sieve.py`](../src/dyadic_sieve.py) enumerates odd multiples of decreasing powers of two, appending zero last. It yields integers via `keys(n_bits)` or most-significant-bit-first lists via `vectors(n_bits)`, suitable for conversion to PyTorch tensors. For four bits the sequence begins `1000, 0100, 1100, 0010, 0110, 1010, 1110`. It is iterative, not recursive.

**Python tests.** [`tests/test_dyadic_sieve.py`](../tests/test_dyadic_sieve.py) checks the four-bit ordering, uniqueness/completeness for bit widths 0 through 8, and negative-width rejection. The user reported all three tests passing.

**Lean formalization.** [`lean/DyadicSieve.lean`](../lean/DyadicSieve.lean) defines $\mathrm{sieveKey}(k,i)=(2i+1)2^k$ and proves:
- Injectivity of odd multipliers and uniqueness of samples within a level.
- **Global uniqueness**: equal positive sieve keys imply equal level and index.
- Positivity of generated sieve keys; zero is handled separately in Python.
- A conditional cluster-hit lemma: a bounded forward-gap assumption implies every sufficiently wide interval contains a sample.
- A simple repeated-draw counterexample for sampling with replacement, plus the dyadic refinement identity.

At this stage the user confirmed a successful seven-job Lean build. Subsequent modules and their final verification are recorded below.

**Scope of these initial proofs.** The uniqueness theorem covers the mathematical sampling formula; the bounded Python generator and exactly-once zero still lack a direct end-to-end correspondence proof. The gap lemma is conditional. Later sections establish the exact solid-cluster first-hit sum for power-of-two lengths using a formalized finite sieve order. Random sampling *without* replacement also avoids duplicates.

## Possible future directions

The power-of-two solid-cluster expectation proof is complete for `m≥2` (see the final entry below). Further proofs are **optional**, not prerequisites for exploring VQA applications:

- Try the sieve as a candidate-bitstring exploration strategy in a concrete VQA experiment with `pytorchqbit` or an IQM example.
- Study non-power-of-two cluster sizes, random cluster-location distributions, and practical evaluation cost.
- If useful later, formalize the `m=1` case, a direct Python–Lean correspondence, and worst-case discovery bounds.

## Verification commands

From the repository root:

```bash
python -m unittest discover -s tests -v
lake -d lean build
```


## 2026-11-19 — Expected time to find a solid cluster

Model: $N=2^n$ keys, one contiguous interesting interval of length $m$, and a uniformly random interval start among $N-m+1$ possibilities. For each start $a$, $T(a)$ is the 1-based index of the first sieve key in $[a,a+m)$.

The **exact** expected number of trials is

```math
\mathbb{E}[T]=\frac{1}{N-m+1}\sum_{a=0}^{N-m}T(a).
```

The comparison baselines are $N/m$ for independent uniform random draws **with replacement**, and $(N+1)/(m+1)$ for a uniformly random permutation (**without replacement**).

Added [`src/cluster_expectation.py`](../src/cluster_expectation.py) to calculate this exact rational number by exhaustive cluster-start enumeration, with [tests](../tests/test_cluster_expectation.py) cross-checking against direct scanning. For `N=16` the expected sieve trial counts are `m=1: 17/2`, `m=2: 64/15`, `m=3: 22/7`, `m=4: 28/13`, and `m=16: 1`.

Added [`lean/ClusterExpectation.lean`](../lean/ClusterExpectation.lean) with finite-sum upper-bound and pointwise comparison lemmas, and included it in the Lake build. The user confirmed the seven Python tests and a successful Lean build after initial fixes. Later Lean modules prove that the actual finite sieve ordering yields the same summed first-hit times; see the final entry.

At this point in the journal the concrete first-hit sum was not yet formalized; it is now verified in `FirstHitSum.lean` (last entry).

## 2026-11-19 — Power-of-two solid-cluster closed form

For $N=2^n$, a contiguous cluster of length $m=2^r$, and a uniformly random start among $N-m+1$ possible positions, the exact first-hit sum for the dyadic sieve follows the formula

```math
S(N,m)=\frac{N(N-m+2)}{2m}.
```

Consequently, the expected first-hit trial is

```math
\boxed{\mathbb{E}[T]=\frac{N(N-m+2)}{2m(N-m+1)}}.
```

**Arithmetic-series derivation.** Set $q=N/m$. For the dyadic midpoint order, exhaustive results show the following first-hit histogram over all $N-m+1=m(q-1)+1$ possible cluster starts: exactly $m$ starts are first hit on each trial $t=1,\ldots,q-1$, and the one remaining boundary start is first hit on trial $q$. Thus

```math
\begin{aligned}
S &= m\sum_{t=1}^{q-1}t+q \\
  &= \frac{mq(q-1)}{2}+q \\
  &= \frac{q(mq-m+2)}{2} \\
  &= \frac{N(N-m+2)}{2m},\\[4pt]
\mathbb{E}[T] &= \frac{S}{N-m+1}
              = \frac{N(N-m+2)}{2m(N-m+1)}.
\end{aligned}
```

This is an **arithmetic sum** derivation, not a geometric series. The formula agrees with direct exhaustive enumeration and is checked in `tests/test_cluster_expectation.py` for power-of-two `N≤512` and every power-of-two `m≤N`. The Python module exposes `power_of_two_cluster_expectation` and `power_of_two_cluster_sum`.

**Lean status.** [`lean/ClusterExpectation.lean`](../lean/ClusterExpectation.lean) now includes `triangular_double_succ`, `powerTwoClusterTrialTotal_succ`, and `powerTwoClusterTrialTotal_formula`. These establish the arithmetic-series identity and closed form *given the first-hit histogram*. The user reported that the updated Lean build appeared successful. **Historical note:** the connection to the concrete order was unfinished at this stage, but the final entry documents its later machine-checked completion for `m≥2`.

For $1<m<N$, this expectation is strictly less than the uniform-random-permutation baseline $(N+1)/(m+1)$. The difference simplifies to

```math
\frac{N+1}{m+1}-\mathbb{E}[T]
=\frac{(N-m)(N+2)(m-1)}{2m(m+1)(N-m+1)}>0.
```

At $m=1$ and $m=N$, the expectations agree.

**Current status:** the actual first-hit **sum identity** is now proved end-to-end for power-of-two `m≥2`; the uniform expectation follows by dividing by the number of cluster starts. An explicit rational-valued expectation theorem and arbitrary non-power-of-two lengths are outside the present Lean development.


## 2026-11-19 — Deriving the histogram from the actual sieve order

The combinatorial argument behind the power-of-two closed form is now explicit. Put `N=2^(n+r)`, `m=2^r`, and `q=2^n`. The positive-key order admits the exact recurrence:

```text
positiveSieve(0)     = []
positiveSieve(n + 1) = [2*x for x in positiveSieve(n)]
                       ++ [1, 3, ..., 2^(n+1)-1].
```

This is the same coarse-to-fine order as Python's `keys(n)` before the final zero. In particular, its first `q-1` samples are `m` times the positive `n`-bit sieve order, so they are precisely the nonzero multiples of `m`, without repetition. For `m>1`, the next sample (trial `q`) is `m/2`; for `m=1`, trial `q=N` samples the final zero.

For each multiple `j*m` with `1<=j<q`, exactly `m` cluster starts are associated with it: `(j-1)*m+1, ..., j*m`. A solid length-`m` cluster from any of these starts contains `j*m` and no other nonzero multiple of `m`. The only other start is zero; its first hit occurs at trial `q`. Hence the first-hit histogram has `m` occurrences of every trial `1,...,q-1` and one occurrence of trial `q`, establishing the arithmetic-series formula recorded above.

Added [`lean/SieveHistogram.lean`](../lean/SieveHistogram.lean) to formalize the recursive finite order, key bounds, completeness and nonduplication, the scaled prefix, the next sample, and the uniqueness of the positive-prefix hit for each cluster-start block. The theorem `positiveSieve_histogram_certificate` combines those facts for power-of-two `m>1` as a statement about the actual sampled keys. This is the **direct connection to the concrete ordering** that was previously missing. The remaining step at the time was to define numerical first-hit times and prove their total. Both the structural module and the subsequent first-hit sum module were ultimately **confirmed to compile** (19-job Lean build). The `m=1` case remains outside the final summed theorem.

As an independent implementation cross-check, the same recursive positive-key construction matched Python's level-based generator for bit widths 0 through 9.

## 2026-11-19 — End-to-end expected first-hit sum proved in Lean

**Verified result.** Added [`lean/FirstHitExpectation.lean`](../lean/FirstHitExpectation.lean) and [`lean/FirstHitSum.lean`](../lean/FirstHitSum.lean). The user ran `lake -d lean build` and reported **“Build completed successfully (19 jobs)”**, including `FirstHitSum`, without errors or warnings.

The proof no longer assumes a first-hit histogram. It defines `firstHitTrial` on the concrete finite dyadic sieve, proves the hit ranks for all positive cluster starts, handles the zero-start boundary cluster, partitions all valid starts into blocks, and shows that the resulting sum equals the previously proved weighted rank total.

For `N=2^k` and `m=2^r` with **`2≤m≤N`**, a cluster occupies `[a,a+m)`, with `a` ranging over all `N-m+1` valid starts. The Lean theorem `actualFirstHit_total_formula` proves the integer identity

```math
2\sum_{a=0}^{N-m} T(a)
=\frac{N(N-m+2)}{m}.
```

Equivalently, the exact total is

```math
S(N,m)=\sum_{a=0}^{N-m}T(a)=\frac{N(N-m+2)}{2m}.
```

Assuming a **uniform distribution over the possible starting positions**, dividing by their count yields the expected trial number:

```math
\boxed{\mathbb{E}[T]=\frac{N(N-m+2)}{2m(N-m+1)}}.
```

Lean checks the **integer sum theorem** from the actual sieve ordering. The rational division displayed above is its mathematical corollary; a separate rational-valued Lean theorem was not added.

Key machine-checked statements: `positiveSieve_histogram_certificate` (finite sieve structure), `firstHitTrial_block` and `firstHitTrial_boundary` (first-hit ranks), `actualFirstHit_total` (sum over all cluster positions equals weighted rank total), and `actualFirstHit_total_formula` (closed form).

**Scope and stopping point.** This completes the intended mathematical argument for solid power-of-two clusters of length at least two. The singleton case `m=1` has expectation `(N+1)/2` for any permutation of `N` keys, but is not covered by this final Lean theorem because the Python algorithm yields zero last. Non-power-of-two lengths can still be evaluated exactly with `src/cluster_expectation.py`. No further formal proofs are planned for now; focus can shift to VQA experiments.

## 2026-11-19 — Recursively ordered dyadic sieve variant

Added [`src/recursive_dyadic_sieve.py`](../src/recursive_dyadic_sieve.py) as a **second algorithm**, without changing [the original sieve](../src/dyadic_sieve.py). Both visit the same coarse-to-fine refinement levels, but the original enumerates keys in ascending order within each level, whereas the new variant enumerates the indices at each level in **bit-reversal order**. This is the finite base-2 van der Corput order with zero placed last.

For four bits:

```text
                    original                 recursively ordered
level 0             8                        8
level 1             4, 12                    4, 12
level 2             2, 6, 10, 14             2, 10, 6, 14
level 3             1, 3, 5, 7, 9, 11, 13, 15 1, 9, 5, 13, 3, 11, 7, 15
last                0                        0
```

The within-level permutation is computed iteratively by reversing the `level` index bits; no recursion depth or external dependency is required. Both implementations expose `keys(n_bits)` and MSB-first `vectors(n_bits)`.

This matters for **non-solid successful sets**: on 4 bits, successful keys `{6, 14}` are hit on trial 5 by the original sieve and trial 6 by the recursive variant, whereas `{10, 14}` reverses the advantage (trials 6 versus 5). For uniformly located **solid clusters of power-of-two length**, the exact average remains the same because the order only permutes the first `N/m-1` positive multiples of `m`; this preservation has been **checked in Python**, not separately proved for the variant in Lean.

Added [`tests/test_recursive_dyadic_sieve.py`](../tests/test_recursive_dyadic_sieve.py) to check the four-bit sequence, complete coverage and uniqueness, equivalence of refinement-level sets, examples of non-solid first hits, and the expected-time formula for power-of-two solid clusters. The six new tests passed in a local Python test run. The existing Lean formalization concerns the original ordering; no additional proofs are planned for this variant at present.

## 2026-11-19 — Comparing dyadic sieves against VQA-assisted binary search

**Question.** When the objective is a function of an `n`-bit vector,

```math
f:\{0,1\}^n\to\mathbb{R},
\qquad
\text{hit}(x)\iff f(x)\leq\tau,
\qquad N=2^n,
```

how many objective evaluations does either sieve need before finding a hit, compared with a VQA that uses binary search to refine its search?

**Baseline from this project.** For a single uniformly placed *solid contiguous interval* of `m=2^r >= 2` hits in **integer bitstring order**, both sieve variants have expected first-hit count

```math
\mathbb{E}[T_{\mathrm{sieve}}]
=\frac{N(N-m+2)}{2m(N-m+1)}
\approx\frac{N}{2m}\quad(N\gg m).
```

This counts **individual, deterministic objective evaluations**, stopping at the first hit. The formula is machine-checked for the original sieve's total over cluster positions (uniform averaging is a mathematical corollary); the recursive variant was checked numerically in Python. It is **not** a generic bound for irregular hit sets or arbitrary VQA cost functions.

**Binary search needs a richer oracle.** A midpoint evaluation returning only `hit(x) = false` cannot say whether a target interval is left or right of `x`. Even an unknown single contiguous cluster is **not enough** to justify `O(log N)` midpoint search with mere membership queries. If an algorithm can reliably answer **which half contains a solution**, the candidate bitstring region may instead be reduced in `O(log N)` such *decisions*; each directional decision's cost must be accounted for. For example, a known monotonic or unimodal objective can sometimes provide directional information, but a generic black-box binary-vector objective cannot.

**Related published VQA hybrid.** [Soltaninia and Zhan (2025), *Quantum global minimum finder based on variational quantum search*](https://www.nature.com/articles/s41598-025-91407-z), proposes **QGMF**, using binary search to choose a **shift of the objective-value threshold**, followed by variational quantum search for marked values. It does **not** simply bisect the integer ordering of candidate bitstrings. Logarithmic threshold-selection steps do not imply logarithmic end-to-end VQA cost because each step calls a variational search routine with optimization and measurement overhead. [Recursive QAOA](https://link.springer.com/article/10.1140/epjqt/s40507-023-00214-w) offers a different route: reduce a combinatorial problem through correlations from quantum measurements, rather than searching numeric input halves.

**Illustrative counts (not a benchmark).** Choose `n=16`, `N=65,536`, and a contiguous hit region of length `m=256`.

| Method | Idealized search work | Interpretation |
| --- | --- | --- |
| Either dyadic sieve | About **128** evaluations on average | Uniformly positioned solid interval; one classical check per key |
| Binary search with correct half-membership/direction information | At most **16** decisions to isolate a key | **Not** available from ordinary hit/miss evaluations; decisions may be expensive |
| VQA + threshold binary search | Number of threshold decisions **times** variational-search cost | No universal speedup or simple fixed evaluation count |
| Grover search | `O(sqrt(N/m)) = O(16)` coherent oracle queries | Ideal marked-state quantum oracle; not a performance guarantee for VQAs |

Grover's comparison concerns **coherent quantum oracle calls**, not circuit runs of the same cost as classical evaluations. The real resource measure should record objective-function queries, optimizer iterations, quantum circuit executions and shots, oracle/embedding overhead, wall-clock time, and achieved hit probability separately. For example, **16** outer decisions requiring **100** optimization iterations with **100** shots each would consume **160,000** circuit shots, *hypothetically*, before other overhead.

**Research direction; no new proof required.** Test VQA/QAOA as a **region-proposal mechanism** followed by either the original or recursive dyadic sieve inside promising regions. Also compare sieve-selected restarts against purely random, Sobol, or Halton initializations. An instructive first experiment would compare a known contiguous hit region with fragmented/non-solid regions, holding total classical evaluations or circuit-shot budgets and desired success probability fixed. **No VQA hybrid or benchmark is implemented yet**, and the new comparison is a proposal rather than a demonstrated speedup. External pointers are collected in [neighbors.md](neighbors.md).

## 2026-11-19 — First runnable VQA draft with recursive-sieve angle search

Implemented [`src/sieve_qaoa.py`](../src/sieve_qaoa.py) and
[`examples/sieve_qaoa_maxcut.py`](../examples/sieve_qaoa_maxcut.py).
This is a genuine **one-layer QAOA ansatz**, simulated with a
dependency-free, exact classical statevector rather than quantum hardware.
The problem is a cost `f(x)` over binary solutions `x`, and the **free
variational angles** `gamma` and `beta` are selected by the existing
[`recursive_dyadic_sieve.keys`](../src/recursive_dyadic_sieve.py).

For a diagonal cost Hamiltonian `H_C |x> = f(x) |x>`, the ansatz and its
energy are

```math
|\psi(\gamma,\beta)\rangle
= e^{-i\beta\sum_{j=0}^{n-1}X_j}
  e^{-i\gamma H_C}|+\rangle^{\otimes n},
\qquad
E(\gamma,\beta)
= \sum_{x\in\{0,1\}^n} f(x)\,|\langle x|\psi(\gamma,\beta)\rangle|^2.
```

**Search strategy.** The angles are discretized as
`theta_k = 2*pi*k / 2**angle_bits`. The recursive sieve orders the
candidate `k` values coarse-to-fine. The optimizer first scans `gamma`
while holding `beta` fixed, then scans `beta` while holding `gamma`
fixed; it repeats this coordinate search for the requested number of
sweeps. The initial angles are nonzero to avoid the flat single-parameter
search produced by starting this one-layer ansatz at both angles zero.
`target_energy` can stop a search once a **sufficiently low expected
energy** is found, and `max_evaluations` caps total exact energy
evaluations. Neither is a Grover oracle.

**Four-vertex MaxCut example.** The objective is the negative number of
cut edges on the cycle `0-1-2-3-0`. With `angle_bits=4` and `sweeps=2`,
the local noiseless simulation reported:

- Initial expected energy: **-1.0**.
- Optimized expected energy: **-3.0**.
- Optimized angles: `gamma ≈ 2.35619`, `beta ≈ 0.39270`.
- **65** exact statevector energy evaluations (one initial point plus
  four scans of 16 grid angles).
- The most likely measured binary strings are `0101` and `1010`,
  each with probability approximately **0.266**, corresponding to
  maximum cuts of four edges. Their combined probability is about
  **0.531**, not certainty of observing a ground-state bitstring.

Seven dedicated tests in [`tests/test_sieve_qaoa.py`](../tests/test_sieve_qaoa.py)
passed locally, covering the cost encoding, state normalization,
uniform output at zero cost angle, actual energy improvement, sieve
invocation, early stopping, budget, and invalid input handling. No Lean
work was added.

**Scope and interpretation.** The sieve searches **VQA circuit angles**;
the QAOA output distribution samples **binary solutions**. A full scan
of the same finite angle grid has the same candidates regardless of
permutation: the recursive ordering can change *time to a target* or
the outcome under a finite candidate budget, not the best value
after an exhaustive scan. Exact statevector evaluation already
enumerates `2^n` cost values and amplitudes, so these figures are
**not hardware shot counts, scaling results, or a quantum advantage**.
Future experiments could replace the exact simulator with a shot-based
quantum backend and compare recursive sieve, original sieve, uniform
grid, random, Sobol, and classical VQA optimizers at matched budgets.

## 2026-11-19 — Session wrap-up and handover

Research and implementation are **paused at a reproducible first prototype**. The repository now contains the original and recursively ordered dyadic sieves, the completed Lean first-hit **integer sum** theorem for the original sieve (owner-confirmed successful 19-job build), and an initial exact-statevector **one-layer QAOA** experiment whose free angles are chosen by the recursive sieve. No additional mathematical proofs, hardware integration, or optimizer benchmark has been completed in this wrap-up.

The MaxCut simulation in [`examples/sieve_qaoa_maxcut.py`](../examples/sieve_qaoa_maxcut.py) is the current demonstration; [`src/sieve_qaoa.py`](../src/sieve_qaoa.py) supports target-energy and evaluation-budget stopping. The previous session reported **seven dedicated Python QAOA tests passing locally**, but the owner has not yet reported independent results for the latest Python draft. Earlier Lean verification does not establish the runtime behavior of the new QAOA code.

**Research takeaway:** the sieve ordering is most relevant when searching for an acceptable angle under a **limited objective-evaluation budget or early stopping**. Exhaustively scanning an identical grid erases the ordering advantage for the grid's best attained energy. The ideal statevector evaluation count cannot be compared directly with physical QAOA shot counts, and the proven one-dimensional solid-cluster formula does not imply a quantum speedup or general benefit on irregular, multidimensional VQA landscapes.

A copy-ready next-conversation prompt, source map, verified-versus-reported status, and restart commands are saved in **[`docs/handover.md`](handover.md)**. On resuming, start there and confirm tests before proceeding with any fair optimizer comparison. Further development is deferred until the owner chooses a new task.

## 2026-11-20 — Optimizer benchmark, verification, and preprint record

**Benchmark implementation and results.** Added [`src/qaoa_benchmark.py`](../src/qaoa_benchmark.py), [`examples/benchmark_qaoa_optimizers.py`](../examples/benchmark_qaoa_optimizers.py), and [`tests/test_qaoa_benchmark.py`](../tests/test_qaoa_benchmark.py). The [benchmark notes](qaoa_benchmark.md) describe five small MaxCut graphs, three starting angles per graph, a 16-point-per-coordinate angle grid, and a 65-exact-evaluation budget. The study compares the recursive sieve, original sieve, ascending and shuffled coordinate ordering, random joint-angle sampling, and a basic derivative-free pattern search. Twelve seeds per graph/start are used for the two randomized methods, giving **420 recorded runs** in total. [Paper data and reproduction instructions](../paper/README.md) are checked in.

**Preliminary findings.** The recursive and original sieve scans reach the retrospective target in **60.0%** of the 15 deterministic graph/start trials by 10 evaluations and **86.7%** by 65 evaluations, identical in aggregate despite some different individual first-hit ranks. The pattern-search baseline reaches the target in **40.0%** by 10 evaluations and **100%** by 20; it also escapes some unfavorable coordinate-scan starts. The benchmark sets targets using an offline exhaustive 16×16 reference grid, **not counted in individual optimization budgets**. Exact statevector evaluations are **not physical quantum shots**, and no universal ordering or quantum advantage follows from these small examples. Full methodology, limitations, and other baselines are recorded in [`qaoa_benchmark.md`](qaoa_benchmark.md).

**Independent owner-reported build and tests.** Pauli Rikula ran `lake -d lean build`, which completed successfully with **19 jobs** (including `SieveHistogram`, `FirstHitExpectation`, and `FirstHitSum`), and `python -m unittest discover -s tests -v`, which reported **29 tests passing** in **0.409 s**. These results were supplied by the owner and are distinct from the local numerical cross-checks and benchmark-only tests performed during manuscript preparation. No new Lean proofs were added. The main result formalized in Lean remains the original sieve's **integer first-hit sum identity**; the expectation is the corresponding mathematical corollary under uniformly positioned contiguous power-of-two clusters.

**Research note and preprint.** Prepared a five-page manuscript titled *Coarse-to-Fine Dyadic Sampling: An Exact First-Hit Result and an Exploratory QAOA Benchmark*, credited to **Pauli Rikula** with no affiliation. The repository contains the [PDF](../paper/dyadic_qaoa_note.pdf), [LaTeX manuscript](../paper/source/dyadic_qaoa_note.tex), plotting and verification scripts, raw/summary CSVs, and an AI-use declaration at the end of the paper. The author supplied the **[Zenodo preprint record link](https://zenodo.org/records/24382960)**. This journal records the provided URL, without independently asserting Zenodo metadata or a DOI. GitHub currently reports the repository is **public**.

**Possible next experiment, not implemented.** Combine **recursive dyadic global sampling with multistart pattern search**, and compare it at matched total exact-energy budgets against the original-sieve and random multistart versions. The goal would be to isolate the contribution of starting-point order from the benefit of local optimization itself. No results for this hybrid exist yet; retain the current preprint's distinction between established results, exploratory observations, and future work.


## 2026-11-21 — Global pilots followed by pattern search

The [follow-up study](../paper/hybrid/README.md) reconstructs the historical overtake at call 14. It tests seven pilot schedules, a fixed fraction, a patience rule and a two-action checkpoint learned from the five original graphs. Each run starts a single local search from the best pilot point. Data cover two new sets of 24 connected MaxCut graphs, three common starts, and budget and grid sensitivity checks. The 59,595 rows are paired policy runs. Uncertainty is calculated at graph level.

On the fresh confirmation set, the 13-call Halton pilot hit 63/72 targets by call 20 and 66/72 by call 65. The 33-call pilot hit 58/72 by 20 and all 72 by call 28, during sampling. Immediate pattern search, four-call Halton patience and the learned Halton checkpoint finished at 49/72, 37/72 and 57/72. A MaxCut mixer symmetry explains why both joint dyadic pilots expend early queries on equivalent beta angles with the tested encoding. The [new paper](../paper/hybrid/hybrid_qaoa.pdf) gives a finite-budget switching criterion and the paired uncertainty estimates.
