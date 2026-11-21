# When should a sieve hand off to pattern search?

[Research draft (PDF)](hybrid_qaoa.pdf) · [Editable LaTeX](hybrid_qaoa.tex) · [Method-level results](results/summary.csv) · [Paired uncertainty intervals](results/paired.csv)

The optimizer spends a configurable fraction of a finite energy-call budget sampling a periodic pair of QAOA angles. It runs one pattern search from the best sampled point. Each global or local objective query counts, including repeated polls. Local convergence can leave calls unused.

The archived first-hit records put the later overtake on call 14. A 13-call pilot includes initialization and leaves 52 of 65 calls available for local polling. With Halton starts, that split hit the target in 70/72 cases on cohort A and 66/72 on fresh cohort B. A 33-call Halton pilot hit all 72 targets in each cohort during sampling. Immediate polling hit 50/72 and 49/72. On cohort B the 13-call split led the 33-call split at call 20 (63 hits versus 58). Both adaptive Halton rules lost final target coverage against fixed 13. These are exact-statevector MaxCut experiments on a specified grid, with offline reference targets.

## Use the optimizer

From the repository root, with Python 3.11+ and no extra runtime dependencies:

```bash
PYTHONPATH=src python - <<'PY'
from hybrid_qaoa import optimize_hybrid
from sieve_qaoa import maxcut_costs

costs = maxcut_costs(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
run = optimize_hybrid(costs, starter="halton", pilot_fraction=0.2,
                      max_evaluations=65, initial=(2, 1))
print(run.best_angles, run.best_energy, run.pilot_calls, len(run.trials))
PY
```

`initial` holds grid indices. The result returns the best angles in radians. `starter` accepts `original`, `recursive`, `halton`, `sobol`, `random`, `original_coordinate` and `recursive_coordinate`. Use `seed` for the random sequence. The default is fixed Halton with a 20% pilot. Use `pilot_fraction=33/65` for the longer tested split. With no adaptive rule, zero selects immediate polling and one selects uninterrupted sampling.

For the patience policy, pass `pilot_fraction=0.4, patience=4`. For the learned Halton policy, pass `pilot_fraction=13/65, switch_when=CheckpointSwitch(switch_if_improving=True, switch_if_stale=False)`, importing `CheckpointSwitch` from `hybrid_qaoa`. It makes one decision on call 8 using the improvement since call 4. The fitted actions for every starter are in [checkpoint_rules.csv](results/checkpoint_rules.csv). For other objectives on the same periodic grid, `search_grid` accepts an integer-indexed energy callback.

## Reproduce

From the repository root:

```bash
python -m unittest discover -s tests -v
python examples/benchmark_hybrid_qaoa.py
python paper/hybrid/analyze.py
cd paper/hybrid
pdflatex -interaction=nonstopmode -halt-on-error hybrid_qaoa.tex
pdflatex -interaction=nonstopmode -halt-on-error hybrid_qaoa.tex
```

The benchmark uses the standard library. Analysis and figure generation use NumPy, pandas and Matplotlib. The included figures and table rows also allow a direct PDF build with a standard TeX Live installation. To reproduce into another location, pass `--out DIR` to the benchmark and `--results DIR --figures FIG_DIR` to the analysis.

| File | Contents |
| --- | --- |
| [runs.csv.gz](results/runs.csv.gz) | One row per case, start, starter, seed and policy, including stage lengths, target, first hit, energies and the call-8 feature when observable. Empty first hit means the target was missed. |
| [graphs.json](results/graphs.json) | Graph membership, edges, size/density stratum and generation seed. |
| [historical_crossover.csv](results/historical_crossover.csv) | Exact per-call cumulative first-hit counts reconstructed from the first study. |
| [calibrated_splits.csv](results/calibrated_splits.csv) | Smallest loss-minimizing genuine hybrid split in the historical cases for each starter and its cohort A performance. |
| [checkpoint_rules.csv](results/checkpoint_rules.csv) | Training counts, paired losses and chosen action in each of two states. |
| [summary.csv](results/summary.csv) | Hit rates by 20 and by the cap, capped first-hit time, terminal normalized gain, and mean actual pilot/total costs. |
| [paired.csv](results/paired.csv) | Mean policy differences and percentile intervals from 10,000 stratified graph-cluster bootstrap draws. |

The 59,595 rows comprise 7,845 historical calibration runs, 38,952 cohort A main runs, 7,848 cohort B confirmation runs, 3,960 shorter-budget runs, and 990 finer-grid runs. A pure-pattern row represents the shared baseline across starters. The same random seeds pair policies within a graph/start. The primary loss scores a missing hit as budget + 1. The energy target is 80% of the way from the initial energy to the exhaustive grid minimum.

The benchmark replays exact statevector grid tables for speed. The optimization interface receives one queried value at a time. The exhaustive minimum is available only to the offline scorer. All 1,923,025 logical calls are charged to the respective traces, including revisits. The study uses 53 tables of 256 cells and six additional tables of 1,024 cells. Its submission status is a project research draft.
