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

**Lean formalization.** [`lean/DyadicSieve.lean`](../lean/DyadicSieve.lean) defines $\mathrm{sieveKey}(k,i)=(2i+1)2^k$ and proves:
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


## 2026-11-19 — Expected time to find a solid cluster

Model: $N=2^n$ keys, one contiguous interesting interval of length $m$, and a uniformly random interval start among $N-m+1$ possibilities. For each start $a$, $T(a)$ is the 1-based index of the first sieve key in $[a,a+m)$.

The **exact** expected number of trials is

```math
\mathbb{E}[T]=\frac{1}{N-m+1}\sum_{a=0}^{N-m}T(a).
```

The comparison baselines are $N/m$ for independent uniform random draws **with replacement**, and $(N+1)/(m+1)$ for a uniformly random permutation (**without replacement**).

Added [`src/cluster_expectation.py`](../src/cluster_expectation.py) to calculate this exact rational number by exhaustive cluster-start enumeration, with [tests](../tests/test_cluster_expectation.py) cross-checking against direct scanning. For `N=16` the expected sieve trial counts are `m=1: 17/2`, `m=2: 64/15`, `m=3: 22/7`, `m=4: 28/13`, and `m=16: 1`.

Added [`lean/ClusterExpectation.lean`](../lean/ClusterExpectation.lean) with finite-sum upper-bound and pointwise comparison lemmas, and included it in the Lake build. The user confirmed the seven Python tests and a successful Lean build after initial fixes. Later Lean lemmas also prove the arithmetic-series closed form from a proposed first-hit histogram, but the histogram has not yet been proved from the actual sieve sequence.

Next proof task: formalize first-hit times of the bounded dyadic sequence, prove its cluster-start histogram for power-of-two `m`, and then extend the analysis to arbitrary `m`.

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

**Lean status.** [`lean/ClusterExpectation.lean`](../lean/ClusterExpectation.lean) now includes `triangular_double_succ`, `powerTwoClusterTrialTotal_succ`, and `powerTwoClusterTrialTotal_formula`. These establish the arithmetic-series identity and closed form *given the first-hit histogram*. The user reported that the updated Lean build appeared successful. **Still unproved in Lean:** that the concrete dyadic sampling order has the required histogram, hence a fully machine-checked end-to-end expected-time theorem.

For $1<m<N$, this expectation is strictly less than the uniform-random-permutation baseline $(N+1)/(m+1)$. The difference simplifies to

```math
\frac{N+1}{m+1}-\mathbb{E}[T]
=\frac{(N-m)(N+2)(m-1)}{2m(m+1)(N-m+1)}>0.
```

At $m=1$ and $m=N$, the expectations agree.

**Open formalization:** derive the histogram directly from the bounded dyadic sampling sequence in Lean, and prove the rational expectation/comparison theorem end-to-end. Non-power-of-two cluster lengths still use the exact finite-sum algorithm.
