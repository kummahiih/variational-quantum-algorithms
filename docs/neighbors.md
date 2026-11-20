# Neighbors

Related SDKs, examples, and repositories to consult while studying variational quantum algorithms. These are references, not project dependencies.

## IQM SDKs and examples

- [IQM SDK documentation](https://docs.iqm.tech/) — entry point for IQM client-side libraries, including IQM Client and QAOA.
- [IQM SDK source/documentation repository](https://github.com/iqm-finland/sdk) — IQM's SDK documentation repository.
- [IQM QAOA documentation](https://docs.iqm.tech/iqm-qaoa/) — QAOA library for IQM systems.
- [Training the QAOA](https://docs.iqm.tech/4.5/iqm-qaoa/Training%20the%20QAOA.html) — variational parameter training strategies.
- [Sparse MaxCut](https://docs.iqm.tech/4.5/iqm-qaoa/Sparse%20Maxcut.html) — QAOA optimization example.
- [SK Model and Transpilation](https://docs.iqm.tech/4.6/iqm-qaoa/SK%20Model%20and%20Transpilation.html) — hardware-aware QAOA example.
- [Portfolio Optimization](https://docs.iqm.tech/4.6/iqm-qaoa/Portfolio%20Optimization.html) — constrained optimization example.
- [IQM digital-analog VQE examples](https://github.com/iqm-finland/iqm-academy-womanium-hackathon-DAQC-VQE) — educational VQE and digital-analog notebooks.
- [QDMI-on-IQM examples](https://iqm-finland.github.io/QDMI-on-IQM/examples.html) — quantum chemistry / hybrid workflows.
- [IQM Resonance example notebooks](https://github.com/iqm-finland/resonance-example-notebooks) — hardware execution examples.

## Related personal repository

- [pytorchqbit](https://github.com/kummahiih/pytorchqbit) — PyTorch tensor-based qubit states and gates; potential small-scale numerical reference implementation. GPU/autograd suitability remains to be evaluated.


## Parameter sampling and optimization for VQAs

**Published VQA precedents for space-filling initialization**

- [Iannelli & Jansen, *Noisy Bayesian optimization for variational quantum eigensolvers* (2021), arXiv:2112.00426](https://arxiv.org/abs/2112.00426) — Bayesian optimization for VQE; uses quasi-random **Sobol** points to initialize evaluations of the variational parameters. A direct precedent for spreading initial candidates across an angle domain, but not the same deterministic sieve or its cluster-hit bound.
- [Faílde et al., *Using Differential Evolution to avoid local minima in Variational Quantum Algorithms* (2023), Scientific Reports 13:16230](https://www.nature.com/articles/s41598-023-43404-3) — VQE optimization with differential evolution; uses SciPy's **Halton** initialization for its population. The reported performance concerns the full optimizer, not an isolated guarantee for Halton initialization.

**Nearby sampling constructions and software**

- [SciPy: Halton low-discrepancy sequence](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Halton.html) — multidimensional generalization of the van der Corput sequence; useful when exploring several circuit parameters jointly.
- [SciPy: Sobol low-discrepancy sequence](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html) — multidimensional space-filling candidate sequence, including scrambled variants; a useful comparison baseline.
- [SciPy: Quasi-Monte Carlo tutorial](https://docs.scipy.org/doc/scipy/tutorial/stats/quasi_monte_carlo.html) — introduces discrepancy and illustrates Sobol/Halton sampling.

The repository's [dyadic sieve](../src/dyadic_sieve.py) is **closely related to the base-2 van der Corput/bit-reversal construction, but is not exactly the usual van der Corput order**. It enumerates all odd multiples at each dyadic level in increasing numeric order, then advances to the next level and yields zero last. For four bits, its early keys are `8, 4, 12, 2, 6, 10, 14`; conventional base-2 van der Corput (with its zero moved to the end) instead begins `8, 4, 12, 2, 10, 6, 14`. Their *sets* of sampled points agree at complete refinement levels, but within-level ordering differs. The repository now contains [a separate recursive bit-reversal variant](../src/recursive_dyadic_sieve.py) that implements the finite base-2 van der Corput order with zero last. Keep the original and the recursive variant distinct when benchmarking, especially for non-solid successful parameter sets.

**Alternative optimization strategy**

- [PennyLane: Rotosolve optimizer](https://docs.pennylane.ai/en/stable/code/api/pennylane.RotosolveOptimizer.html) — coordinate-wise optimizer exploiting the known trigonometric structure of certain circuit objectives; a more targeted comparator than general-purpose random search when its assumptions apply.
- [PennyLane: quantum circuit structure learning / Rotoselect tutorial](https://pennylane.ai/demos/tutorial_rotoselect) — explains parameter-wise sinusoidal optimization and the related gate-selection strategy.

**Relevance to this repository.** The finite [solid-cluster expected-hit proof](../docs/journal.md) applies to a *one-dimensional contiguous successful interval* with a uniformly located start, for power-of-two lengths `m >= 2`. It does **not** establish superior VQA training performance: VQA objectives are often multidimensional, periodic, noisy, and non-contiguous. An initial one-layer QAOA comparison now exists in [the benchmark notes](qaoa_benchmark.md); broader dyadic-sieve restarts, low-discrepancy multistart, and Rotosolve comparisons remain future work. The sources above establish related approaches, not a formal novelty result about this particular sieve or theorem in VQAs.



## Derivative-free pattern search and low-discrepancy multistarts

**Background and close precedents (not proof of novelty)**

- [Torczon, *On the Convergence of Pattern Search Algorithms* (SIAM Journal on Optimization, 1997)](https://doi.org/10.1137/S1052623493250780) — foundational analysis of derivative-free pattern-search methods. The repository's four-direction polling loop is a deliberately simple *pattern-search-style baseline*, not an implementation of every generalized pattern-search algorithm or its convergence guarantees.
- [Wolniak et al., *Uncertainty propagation via sample-based deterministic model updating for structural damage identification* (Structural Health Monitoring, published online 2025)](https://doi.org/10.1177/14759217251387535) — explicitly combines **Halton sequence** sampling and deterministic **global pattern search** in an engineering model-updating application (HSGPS); also studies a surrogate/meta-model variant. This is a close *sampling + pattern-search* precedent, **not** an experiment on our recursive dyadic order or QAOA angles.
- [*Selective Multistart Optimization Based on Adaptive Latin Hypercube Sampling and Interval Enclosures* (Mathematics, 2025)](https://www.mdpi.com/2227-7390/13/11/1733) — selects promising sample points for local refinement rather than launching an optimizer from every sampled point; discusses random, Halton and Sobol alternatives. A useful design reference for allocating a *shared* function-evaluation budget.
- [SciPy: `differential_evolution` initialization options](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.differential_evolution.html) — built-in `sobol`, `halton`, random and Latin-hypercube initialization demonstrate that low-discrepancy seeds for classical optimization are not novel by themselves. Differential evolution is not the same as pattern search.
- [*Nonsmooth local optimization via direct search* (Optimization Letters, 2026)](https://doi.org/10.1007/s11590-026-02332-7) — explores Sobol/Halton-derived poll directions for derivative-free local search. This is related but **distinct** from using the sieve only to select multistart *initial positions*.

**What is implemented here.** The [first QAOA optimizer benchmark](qaoa_benchmark.md), coded in [`src/qaoa_benchmark.py`](../src/qaoa_benchmark.py), compares six methods on **five small MaxCut graphs × three starts**: recursive and original dyadic coordinate scans, ascending and shuffled scans, random joint-angle evaluations, and a four-direction `pattern` polling baseline. The [raw benchmark CSV](../paper/results/qaoa_benchmark_raw.csv) has **420 rows** (15 per deterministic method, 180 per randomized method). The grid is 16 angles per coordinate, with a cap of **65 exact statevector energy evaluations including initialization** per method/run. Retrospective target thresholds come from an **offline exhaustive 16×16 grid** whose 256 evaluations per graph are not charged to individual optimizers.

The recursive and original sieves **tie in aggregate** (60.0% reach the target by 10 evaluations; 86.7% by 65), while pattern search reaches the target in 40.0% by 10 and 100% by 20 on these 15 graph/start cases. This demonstrates *neither* a universal pattern-search advantage *nor* an independent benefit of one dyadic order. The original and recursive curves coincide in the aggregate figure, so the plot explicitly displays both line styles without offsetting the data.

**Proposed next experiment — NOT implemented:** **Recursive dyadic multistart pattern search** (sometimes shortened to RDMPS). Build a genuine two-dimensional mapping of sieve samples to `(gamma, beta)` *starting pairs*; rank/select starting points if using a pilot stage; then give local pattern-search runs a *shared* global budget. Compare against original-sieve, random, Sobol and Halton multistarts **with the same local search, initial conditions and evaluation accounting**. Charge global-sampling evaluations, local polling, repeated energies, and any selection procedure consistently; specify whether duplicates are cached. Include fixed and periodic angle boundaries, grid resolution, and separate ablations for multistart versus point ordering. The goal is to test an incremental **effect of the sampling schedule**, not to claim invention of multistart or pattern search, a quantum speedup, or even that an exact analogue is absent from the literature. The specific hybrid is **not present in this repository**.

## Variational search, binary search, and recursive reduction

- [Soltaninia & Zhan, *Quantum global minimum finder based on variational quantum search* (2025), Scientific Reports 15:13880](https://www.nature.com/articles/s41598-025-91407-z) — **QGMF** combines variational quantum search (VQS) with binary search over a shift of the **objective-value threshold**. This is closely related to the proposed VQA-plus-binary-search hybrid, but it does **not** binary-search the numerical ordering of bitstring inputs. Each threshold decision depends on a variational quantum search subroutine; logarithmically many threshold adjustments do not by themselves imply logarithmic total circuit cost. [Preprint](https://arxiv.org/abs/2405.00450).
- [*Reinforcement learning assisted recursive QAOA* (2024), EPJ Quantum Technology](https://link.springer.com/article/10.1140/epjqt/s40507-023-00214-w) — discusses **RQAOA**, which iteratively reduces a binary optimization problem by eliminating variables using correlations obtained from quantum states. This is an example of learned reduction, **not** ordinary midpoint binary search in bitstring order.
- [Microsoft Azure Quantum: Theory of Grover's search algorithm](https://learn.microsoft.com/en-us/azure/quantum/concepts-grovers) — reference for the ideal coherent-oracle query scaling `O(sqrt(N/M))` with `M` marked bitstrings among `N`. Oracle synthesis, gate cost, and error correction are additional resource questions; Grover's guarantee should not be attributed to a generic VQA.

## Grover search versus VQA free-parameter optimization

**Keep the two search spaces distinct.** A conventional VQA chooses continuous circuit angles `theta` to reduce an estimated objective such as `E(theta) = <psi(theta)|H|psi(theta)>`, usually with a classical optimizer. **Grover's algorithm does not normally tune those angles**: it amplifies computational-basis states `x` marked by a coherent quantum oracle. These solve different problems even when both are described as "optimization."

- [IBM Quantum: Grover's algorithm tutorial](https://qiskit.qotlabs.org/docs/tutorials/grovers-algorithm) — how an oracle marks **binary solution states** and Grover amplification increases their measurement probability. An ideal query bound is not a VQA parameter-optimization result.
- [Qiskit Optimization: GroverOptimizer / Grover Adaptive Search](https://qiskit-community.github.io/qiskit-optimization/tutorials/04_grover_optimizer.html) — uses **Grover Adaptive Search (GAS)** to seek the minimum of a discrete QUBO cost by adjusting a marking threshold. It is quantum search over encoded **candidate solutions**, not the usual outer-loop adjustment of VQA rotation angles.
- [Golden et al., *Threshold-Based Quantum Optimization* (2021), arXiv:2106.13860](https://arxiv.org/abs/2106.13860) — explores **Grover Mixer Threshold QAOA**, a Grover-inspired *variational ansatz* for optimization. Its mixer and threshold construction do not mean Grover automatically chooses the variational angles.
- [Morales, Tlyachev & Biamonte, *Variationally Learning Grover's Quantum Search Algorithm* (2018), arXiv:1805.09337](https://arxiv.org/abs/1805.09337) — a **reverse-direction** example: optimize a parameterized circuit to learn Grover-like search behavior, rather than invoke Grover to optimize arbitrary VQA parameters.

**Could Grover search over the VQA angles instead?** In principle, discretize `p` angles to `b` bits each, obtaining `2^(pb)` candidate parameter strings, and mark those whose energy is below a threshold. This requires a **coherent, reversible marking oracle for the circuit's objective at each candidate angle**. A VQA's usual sampled energy estimate is not directly such an oracle, so Grover's ideal `O(sqrt(N/M))` query guarantee cannot be transferred to that hybrid without counting oracle construction, approximation, and measurement costs.

**Connection to the two sieves.** Both [ascending-level](../src/dyadic_sieve.py) and [bit-reversal-level](../src/recursive_dyadic_sieve.py) sieves can be tested (1) on **binary solution vectors** `x` scored by a classical objective, or (2) on **discretized VQA angles** `theta`, e.g. a one-angle scan/restart schedule. Their proven solid-interval finding-time result applies to a one-dimensional **integer-ordered** success set, not to generic multidimensional VQA parameter landscapes. For many angles, the mapping from bitstrings to angles and the choice of multidimensional sampling strategy matter.

**Comparison to both dyadic sieves.** With `N=2^n` and `m=2^r >= 2`, and a **uniformly placed contiguous solid cluster** of exactly `m` successful integer-ordered bitstrings, the original sieve's mathematically derived expected number of **classical objective evaluations until the first hit** is

```math
E_{\mathrm{sieve}}=\frac{N(N-m+2)}{2m(N-m+1)}
\approx\frac{N}{2m}\quad(N\gg m).
```

The recursive bit-reversal variant has the same expectation for this special cluster model (numerically checked in Python; not separately formalized in Lean). A classical binary search needs `O(log N)` **directional decisions only if a valid decision oracle can determine which half is still promising**. A plain yes/no hit test at a midpoint gives no such information, even if the successful points form one interval. A VQA subroutine may provide useful guidance but each decision can require many optimizations and circuit shots. Therefore **compare total costs at matched success probability**, rather than comparing sieve point evaluations with a count of binary-search decisions.

A possible hybrid to test: sample promising bitstring regions with VQA/QAOA, then run either sieve within a chosen region; alternatively initialize or restart a VQA from sieve-selected candidates. These specific **hybrids remain research proposals**, not demonstrated speedups or implemented features in this repository; a separate **six-method QAOA baseline benchmark is already implemented**. See the [research journal](journal.md) and [benchmark notes](qaoa_benchmark.md).

Links may target different IQM SDK releases; check version compatibility before using examples.
