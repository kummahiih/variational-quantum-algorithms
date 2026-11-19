# First QAOA optimizer benchmark (2026-11-20)

**Status:** First small, reproducible **noiseless classical simulation** comparison. This is not a hardware experiment or evidence of a quantum speedup. The goal is to study candidate-angle **ordering under limited budgets**, and to expose failure modes before expanding the study.

## Reproduce

From the repository root, with Python 3.11+ and no third-party Python dependencies:

```bash
python examples/benchmark_qaoa_optimizers.py
python examples/benchmark_qaoa_optimizers.py --csv results.csv
python -m unittest discover -s tests -v
```

The benchmark implementation is in [`src/qaoa_benchmark.py`](../src/qaoa_benchmark.py), the example runner in [`examples/benchmark_qaoa_optimizers.py`](../examples/benchmark_qaoa_optimizers.py), and tests in [`tests/test_qaoa_benchmark.py`](../tests/test_qaoa_benchmark.py). The existing [one-layer QAOA simulator](../src/sieve_qaoa.py) and both sieve implementations are **unchanged**.

## Experimental setup

- **Graphs:** `cycle4`, `triangle3`, `path5`, `complete5`, `ladder6` (3–6 qubits).
- **Three common initial angle pairs per graph:** `default` = $(\pi/4,\pi/8)$, `flat_beta` = $(\pi/8,\pi/4)$, `shifted` = $(3\pi/8,3\pi/8)$.
- **Angle grid:** 16 angles per coordinate (`angle_bits=4`), spacing $\pi/8$; default total evaluation cap **65**, including the initial parameter pair.
- **Targets:** for each graph/start pair, an acceptable expected energy is defined by

```math
E_{\mathrm{target}} = E_{\mathrm{initial}}
    -0.8\bigl(E_{\mathrm{initial}}-E_{\mathrm{grid\ ref}}\bigr).
```

  Here $E_{\mathrm{grid\ ref}}$ is the minimum over the **entire 16×16 two-angle grid**. Finding it requires **256 extra exact energy evaluations per graph**. Those *reference computations are not charged to any optimizer's reported budget* and are used only to define evaluation thresholds retrospectively. Therefore this protocol does **not** demonstrate deployable target selection at zero cost.

- **Measurements:** first evaluation to reach the target (if any); hit fraction at evaluation budgets **10, 20, 65**; best energy at 10/20/40/65; probability that the best evaluated QAOA state returns a *globally optimal binary cut* at 65.
- **Fairness:** every method starts at the same angles within a graph/start condition and has the **same ceiling on exact statevector energy evaluations**. Each counted evaluation evaluates a full noiseless statevector; there is **no quantum measurement shot model**. An algorithm that converges early can leave part of its budget unused.

## Methods

| Name | What changes |
| --- | --- |
| `recursive` | Coordinate scan using the recursive bit-reversal dyadic sieve. |
| `original` | **Same coordinate-scan algorithm**, with original ascending-within-level dyadic sieve order. |
| `ascending` | Same coordinate scan, angles visited in increasing numeric order. |
| `shuffled` | Same coordinate scan, angle order shuffled deterministically per scan using a seeded PRNG. |
| `random_joint` | Draw full $(\gamma,\beta)$ angle-grid pairs in seeded random order **without replacement**. This is a separate, two-dimensional search strategy, not a coordinate-order control. |
| `pattern` | Basic deterministic derivative-free coordinate *polling* search: at each step test $\pm h$ along each angle, accept improvements, halve $h$ after unsuccessful polls, and stop at the grid resolution. This is a modest conventional baseline, **not** a claim to implement SciPy/Powell/COBYLA/Rotosolve. |

The stochastic methods are averaged across **12 reproducible seeds per graph/start pair**. All others are run once per graph/start pair. The grid, original, recursive, and shuffled methods have the **same underlying coordinate search**, making them a controlled comparison of candidate ordering. Random joint and pattern search are broader optimizer comparisons.

## First measured results

Results from a local run using Python 3.13, with **5 graphs × 3 starts = 15** graph/start conditions. Deterministic methods have 15 observations each; seeded random methods have 180 each.

| Method | Runs | Hit by 10 evals | Hit by 20 evals | Hit by 65 evals | Mean normalized improvement @ 10 / 65 | Mean optimal-cut probability @ 65 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Recursive sieve | 15 | 60.0% | 66.7% | 86.7% | 71.9% / 93.6% | 56.5% |
| Original sieve | 15 | 60.0% | 66.7% | 86.7% | 71.9% / 93.6% | 56.5% |
| Ascending grid | 15 | 53.3% | 66.7% | 86.7% | 69.2% / 93.6% | 56.5% |
| Shuffled coordinate scan | 180 | 51.1% | 66.7% | 86.7% | 62.3% / 93.6% | 56.5% |
| Random joint pairs | 180 | 52.8% | 71.1% | 95.6% | 73.4% / 97.4% | 59.1% |
| Pattern search | 15 | 40.0% | **100%** | **100%** | 55.0% / 100.0% | 59.7% |

The **normalized improvement** for each run is

```math
G_B = \frac{E_{\mathrm{initial}}-E_{\mathrm{best},B}}
           {E_{\mathrm{initial}}-E_{\mathrm{grid\ ref}}}.
```

It measures the fraction of the initial-to-grid-reference energy reduction achieved by the given evaluation budget. The table shows its arithmetic mean over runs. The optimal-cut probability is evaluated for the best-energy parameter pair at that budget, not the probability of meeting the *energy* target. A high mean over several small graphs must **not** be generalized to arbitrary QAOA landscapes.

### Specific first-hit examples

On `cycle4` from the original default angles, with target $E\le -2.6$ (80% of the initial-to-reference improvement):

- Original sieve reaches the target at evaluation **6**.
- Recursive sieve reaches it at evaluation **7**.
- Ascending grid also reaches it at evaluation **7**.
- Pattern search reaches it at evaluation **2**.

All three complete coordinate grid orders later reach expected energy $-3$. The previously discussed $E\le -2.9$ threshold also has first-hit ranks 6 and 7 for original and recursive respectively.

Two challenging starts illuminate a more serious limitation. From `flat_beta` on `triangle3` and `complete5`, **all four coordinate-order methods** miss the target within 65 evaluations: their coordinate-wise scans fail to escape a plateau. In contrast, pattern search reaches the target after 17 evaluations on each of those cases. Changing the sequence of scanned angles is **not enough** to fix every coordinate-optimization failure.

## Interpretation

1. **No consistent winner:** The recursive and original sieves are tied in aggregate on this small study, though individual *first-hit ranks* differ. For the four-cycle default start, the original is one evaluation faster.
2. **Early stopping matters:** At a fully completed fixed coordinate scan, the candidates are identical regardless of order. Different orders can be useful only before a scan completes or when ties affect the next scan.
3. **Optimization design can matter more than angle order:** Random joint-angle search and simple pattern search both outperform the sieve scans in some conditions. Their methods differ, so one should not attribute the difference solely to candidate permutation.
4. **Initialization matters:** A flat coordinate direction can trap a scan irrespective of its within-coordinate candidate order. A more robust hybrid may require restarts or genuinely multidimensional proposals.
5. **No speedup claim:** Exact statevector evaluations, physical quantum circuit executions, and measurement shots have different resource costs. Comparing only the numbers of evaluations cannot demonstrate a quantum advantage.

## Verification, assumptions, and remaining work

The new tests check: evaluation ceilings and monotonically improving best-so-far traces, random-seed reproducibility, first-hit indices, budget checkpoints, valid probability bounds, reference energies, validation errors, and **agreement between the new recursive trace and the pre-existing QAOA optimizer across all five graphs, three starts, and ten budget checkpoints**.

**Local verification:** 8 dedicated new benchmark tests passed under Python 3.13 in the working environment, and the sample benchmark emitted 420 run records. This does not constitute a remotely executed GitHub CI run or a quantum hardware experiment. Existing simulator source and Lean proofs were not modified.

Before drawing strong conclusions, extend the study with more graph instances and sizes, multiple angle resolutions, confidence intervals across genuinely independent problem/initialization draws, and more capable conventional optimizers. A particularly useful next experiment would combine sieve-ordered proposals with *periodic multistarts*, and compare them at matched objective-evaluation budgets against stronger optimizers. A later shot-noise model should separately report circuit runs and shots; never equate those with an ideal energy evaluation.

See [`docs/working_model.md`](working_model.md) for a detailed conceptual and mathematical explanation of QAOA and the original sieve-tuned prototype.
