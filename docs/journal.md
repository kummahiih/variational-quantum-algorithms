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
