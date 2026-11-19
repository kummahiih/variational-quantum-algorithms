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

The repository's [dyadic sieve](../src/dyadic_sieve.py) is **closely related to the base-2 van der Corput/bit-reversal construction, but is not exactly the usual van der Corput order**. It enumerates all odd multiples at each dyadic level in increasing numeric order, then advances to the next level and yields zero last. For four bits, its early keys are `8, 4, 12, 2, 6, 10, 14`; conventional base-2 van der Corput (with its zero moved to the end) instead begins `8, 4, 12, 2, 10, 6, 14`. Their *sets* of sampled points agree at complete refinement levels, but within-level ordering differs. Do not silently substitute a standard van der Corput generator when benchmarking the exact sieve.

**Alternative optimization strategy**

- [PennyLane: Rotosolve optimizer](https://docs.pennylane.ai/en/stable/code/api/pennylane.RotosolveOptimizer.html) — coordinate-wise optimizer exploiting the known trigonometric structure of certain circuit objectives; a more targeted comparator than general-purpose random search when its assumptions apply.
- [PennyLane: quantum circuit structure learning / Rotoselect tutorial](https://pennylane.ai/demos/tutorial_rotoselect) — explains parameter-wise sinusoidal optimization and the related gate-selection strategy.

**Relevance to this repository.** The finite [solid-cluster expected-hit proof](../docs/journal.md) applies to a *one-dimensional contiguous successful interval* with a uniformly located start, for power-of-two lengths `m >= 2`. It does **not** establish superior VQA training performance: VQA objectives are often multidimensional, periodic, noisy, and non-contiguous. A reasonable future comparison is dyadic-sieve restarts or one-angle scans versus Sobol, Halton, random initialization, and (where suitable) Rotosolve, at matched numbers of circuit evaluations. The sources above establish related approaches, not prior use of this exact sieve and theorem in VQAs.


Links may target different IQM SDK releases; check version compatibility before using examples.
