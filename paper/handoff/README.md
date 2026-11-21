# When should a recursive sieve hand off to pattern search?

This experiment compares **recursive sieve → pattern search** with **random permutation → pattern search**. The primary comparison spends 16 of 65 objective evaluations on each starter. Call 1 pays for the common initial point. Call 17 polls a neighbor of the best point from calls 1–16. The first outcome is the number of calls until either stage evaluates a target.

## Run the comparison

From the repository root, with Python 3.11 or newer, run a two-graph check first. The full run uses 24 calibration graphs, 24 evaluation graphs, three starts per graph and 32 paired placements per start. The runner prints progress after each graph and prints the selected handoff before evaluating it.

```bash
python examples/benchmark_paired_handoff.py --graphs-per-split 1 --draws 1 --out results/handoff-smoke
python examples/benchmark_paired_handoff.py --out results/handoff
```

`--primary 16` sets the fixed comparison. `--pilots 12 14 16 18 20` sets the calibration candidates, which always include the primary. `--budget`, `--draws`, and `--seed` are adjustable. Both starters use each requested length and cap. The two-graph check exercises the pipeline. Use the full run for estimates.

## Matched keyspaces

Each graph supplies an exact one-layer MaxCut QAOA energy for every cell on a periodic $16\times16$ angle grid. Each of the three starts becomes key zero in relative Morton (interleaved-bit) order. For starting energy $E_0$ and offline grid minimum $E_{\min}$, a target is any evaluated cell with energy at most $E_0-0.8(E_0-E_{\min})$ within the optimizer's $10^{-12}$ tolerance.

| Layout | Placement of the same $m$ target energies |
| --- | --- |
| Solid | One consecutive block in linear Morton-key order. Its first key is uniform from $1$ through $256-m$. |
| Isolated | A uniformly drawn size-$m$ subset of keys 1–255 conditional on at least one invalid key between consecutive targets. |

Both placements keep key zero invalid at its original energy. They use the same shuffled lists of target and nontarget energies. Both optimizers receive exactly the same landscape for each layout. The random pilot samples without replacement after the common start. Its permutation seed is shared across pilot lengths and layouts for the same graph, start and draw. The optimizer sees scalar energies. The harness scores target membership afterward. These reindexed landscapes control clustering in key order and change local angle neighborhoods. The [earlier study](../clusters/README.md) also measured native QAOA neighborhoods.

The [shared optimizer](../../src/hybrid_qaoa.py) polls four wrapped angle neighbors from the pilot incumbent, retaining its evaluated energy. Repeated polls cost one call each. At a 16-call recursive handoff on this grid, the pilot has visited the entire $4\times4$ coarse lattice. The four initial local polls at step size four therefore revisit paid cells. The local phase can converge before using all 49 remaining calls.

## Choosing the pilot length

**Coverage when a solid run is known.** With $N$ power-of-two keys and zero paid first, the first $2^j$ recursive probes form a lattice of spacing $N/2^j$. Every linear run at least that long intersects it. A sufficient pilot length for a known lower bound $L$ on the longest run is

```math
D(L)=N/2^{\lfloor\log_2 L\rfloor}.
```

For $N=256$, a 16-key run is covered by call 16 and an 8-key run by call 32. For isolated targets the run-length bound gives 256. For comparison, the random pilot's hit probability by call $k$ in either layout is $1-\binom{N-1-m}{k-1}/\binom{N-1}{k-1}$, conditional on the common invalid start. These are pilot-only statements. A useful local move can make an earlier handoff preferable.

**Timing for the whole hybrid.** Retain $k=16$ as the primary comparison. For a candidate length $k$ let $T_k$ be the first target call of the full recursive hybrid, taking $T_k=\infty$ for a miss. With call budget $B$, choose a common handoff for both layouts by minimizing calibration loss

```math
\hat k=\arg\min_{k\in K}\;\frac{1}{n}\sum_{i=1}^{n}\min(T_{i,k}, B+1),
\qquad K=\{12,14,16,18,20\}.
```

Each graph, start, draw and layout contributes equal weight. A miss after early convergence also scores $B+1$. This loss rewards earlier hits and penalizes failures. Ties favor the length closest to the primary, then the shorter length. Calibration uses only recursive outcomes from the archived cohort named `holdout`. Freeze the choice, then run both starters at the primary and selected lengths on the disjoint archived `confirmation` graphs. The measured widths and target masks are used only for experiment construction and scoring.

## Outputs for the paper

| File | What it measures |
| --- | --- |
| `runs.csv.gz` | One row per paired comparison. Includes placement and order seeds, geometry, budget, actual pilot and local calls, incumbent key and energy at handoff, first local poll key and first target call for each arm. A blank first hit means a miss. |
| `calibration.csv` | Recursive mean loss for each candidate on each layout, their pooled mean, and the frozen choice. |
| `comparison.csv` | Evaluation counts of first hits during the pilot, first hits during polling, and misses. The paired difference in mean loss is recursive minus random, in calls. Negative favors recursive. The 95% percentile interval resamples whole graphs within size/density strata 2,000 times, keeping both methods, starts and placements together. It is blank when a represented stratum has fewer than two graphs. |
| `hit_curve.csv` | Fraction of paired cases that have hit by each paid call, separately for both starters, each layout, and each evaluated handoff. The denominator includes early-converged misses. |

Report the fixed-16 row for each layout first. The calibrated rows measure how well the timing rule transfers across graphs. If calibration also selects 16, one row per layout represents both comparisons.
