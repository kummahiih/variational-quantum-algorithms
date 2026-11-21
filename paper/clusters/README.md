# Clustered versus isolated target keys in QAOA pattern search

[Research paper (PDF)](cluster_assumption.pdf) · [Editable LaTeX](cluster_assumption.tex) · [Simulation driver](../../examples/benchmark_cluster_assumption.py)

Does the opening sieve help when valid keys cluster? Table 1 on **page 1** keeps the 13-call start and the subsequent pattern search fixed and varies the start order. On native QAOA grids with isolated valid keys, the recursive-start hybrid hit **65.3%** versus **91.7%** for Halton. When the same valid energies occupied one planted block, the rates were **79.0%** versus **73.8%**. Immediate pattern search hit 68.1% and 48.3% respectively. The [paired graph analysis](results/paired.csv) measures the change in starter advantage. Table 7 on page 6 gives first hits before and after the handoff on the separate variable-block simulation.

Sections 5–6 cover variable-size solid blocks. The experiment varies the width of a single block across instances and allocates changing totals among several unequal blocks within an instance. It compares nearly equal lengths, random unequal lengths, and one dominant block with the same total, block count, and empty gaps.

## Variable-block simulation

For a 256-key space, the total number of valid keys is uniform on the integers 8–32. For 1,024 keys it is uniform on 32–128. The planted block count is independently uniform on 2–5. Six draws per total/count combination give 600 and 2,328 paired cases per layout respectively. A random unequal allocation draws an ordered positive composition uniformly, conditioning on at least two different lengths. Each run is solid in the integer key order used by the joint dyadic sieve. Placements do not wrap. One variable-width block, explicitly isolated valid keys, and an unrestricted uniform subset provide count-matched controls.

Under the **256-key random unequal model with a 65-call cap**, pure recursive sampling hit 599/600 cases. A 13-call sieve prefix followed by pattern search hit 478/600 with binary feedback and 600/600 when the objective supplied exact toroidal distance to a valid point. Changing the feedback preserves every target location. In a paired example with 19 valid keys and four blocks, the three allocations were `5+4+5+5`, `2+3+13+1`, and `16+1+1+1`.

| Data | What to look up |
| --- | --- |
| [Variable-size run records](results/variable_runs.csv.gz) | Width, planned/actual run count, ordered planted lengths, geometry, paired seed coordinates, both uncapped sieve ranks, three deadlines, and first-hit/full-call counts for 16 policies. |
| [Variable-size method comparison](results/variable_summary.csv) | Capped mean first-hit time, hit rates, and used calls by grid, composition law, feedback and method. |
| [By block count](results/variable_by_count.csv) | The same measurements conditional on the planned number of blocks. |
| [Observed hits and guaranteed deadlines](results/variable_bounds.csv) | The share of each law for which a deadline fits within 65 queries. |
| [Paired comparisons](results/variable_paired.csv) | Bootstrap intervals resampling draws within fixed width/count strata. |
| [All single-block widths](results/variable_single_exact.csv) | Exact mean and maximum for every integer width and every legal position on both grids. |
| [Width priors](results/variable_width_priors.csv) | Mean under uniform widths followed by uniform placement, and under uniform width/start pairs. |

If at least one valid block has length at least $L$, both paid-zero sieves hit by $D(L)=N/2^{\lfloor\log_2 L\rfloor}$. If only total mass $m$ and an upper bound $r$ on the number of runs are known, use $L=\lceil m/r\rceil$. The `recursive_longest_bound` study policy receives the true longest length as an oracle comparison. The nominal `recursive_bound` policy uses the entire valid count as a run length. Its guarantee applies only when the required contiguous run exists. The optimizer can stop at an observed valid point. If a proven deadline exceeds the cap, an earlier first hit is possible but is not certified by that bound.

## Run a case with your own block lengths

This example picks a uniform legal placement conditional on lengths 2, 3, 13 and 1. Change the tuple to simulate a different set of solid blocks.

```bash
PYTHONPATH=src python - <<'PYTHON'
from random import Random
from cluster_landscapes import KeyGrid, coverage_budget, place_runs
from hybrid_qaoa import search_grid

grid = KeyGrid(4)
lengths = (2, 3, 13, 1)
anchors = sorted(Random(7).sample(range(grid.size - sum(lengths) + 1), len(lengths)))
valid = place_runs(grid.size, lengths, anchors)
trace = search_grid(lambda g, b: int(grid.key[g][b] not in valid),
                    angle_bits=grid.bits, initial=(0, 0), starter="recursive",
                    pilot_fraction=1, max_evaluations=65)
print("First valid call", trace.first_hit(0))
print("Guaranteed deadline", coverage_budget(grid.size, max(lengths)))
PYTHON
```

## Exact checks, fixed-size controls, and QAOA

At $N=256,m=16$, the exact first-hit means depend on the assumed target law:

| Placement law | Paid-zero dyadic sieve | Ascending keys |
| --- | ---: | ---: |
| Uniform start of one solid block | 8.97 | 121.00 |
| Uniform unrestricted 16-key subset | 15.12 | 15.12 |
| Uniform 16-key subset with no adjacent keys | 15.17 | 14.24 |

Random ordering of queries and random placement of targets are independent choices. Under the unrestricted uniform law the mean is the same for every fixed permutation. The isolated law forbids adjacency and changes the counting problem. The single-block worst-case bound holds placement by placement. Its quoted mean uses uniform legal starts.

The fixed-size synthetic arm also tests four equal runs and rectangular angle patches with the same mass. A two-qubit one-edge QAOA statevector supplies a physically ordered valid interval. An odd-stride encoding isolates its valid keys while preserving the even queries responsible for every early sieve hit. The archived MaxCut arm preserves exact energy values, the common starting energy and the offline threshold across native, planted-block and shuffled reindexings.

| Data | Contents |
| --- | --- |
| [Exact solid means](results/exact.csv) and [histograms](results/exact_histograms.csv) | All legal starts at powers-of-two sizes 64–4,096, the original zero-last order and the deployed zero-first order. |
| [Exact isolated targets](results/isolated_exact.csv) and [three-law comparison](results/law_comparison.csv) | Counts and exact rational means from a path-counting recurrence, plus uniform-subset controls. |
| [Fixed-size synthetic data](results/synthetic.csv.gz) and [summaries](results/synthetic_summary.csv) | 5,760 matched mask draws, two objective signals and 14 policies. |
| [One-edge circuit](results/one_edge.csv.gz) and [summaries](results/one_edge_summary.csv) | 715 physical placements, each under three key encodings. |
| [Paired archived QAOA data](results/archived_qaoa.csv.gz) and [summaries](results/qaoa_summary.csv) | 24 graphs × 3 starts × 32 draws × 3 layouts, with 14 policies. Reindexing is an offline geometry intervention. |
| [Intervals](results/paired.csv) and [hypothetical mixture](results/mixture.csv) | Paired uncertainty and the conditional recursive-versus-Halton crossover; its [interval](results/mixture_threshold.csv) uses graph-level resampling. |

A missing first-hit field is a miss by the cap, including early local convergence. In the default analyses a miss scores 66. Fields ending in `_used` record all calls used by the full run; the first-hit rank is the cost to a target if the caller stops there. Repeated polls count. Pure fixed schedules are paired across feedback conditions. Seeds, strata and the two grids are kept explicit; no overall performance score pools the placement laws.

## Reproduce

From the repository root, run the variable-block experiment and figures alone:

```bash
python examples/benchmark_cluster_assumption.py --variable-only --out /tmp/variable-blocks
python paper/clusters/analyze.py --variable-only --results /tmp/variable-blocks --figures /tmp/variable-figures
```

For the entire study and paper:

```bash
python -m unittest discover -s tests -v
python examples/benchmark_cluster_assumption.py
python paper/clusters/analyze.py
cd paper/clusters
pdflatex -interaction=nonstopmode -halt-on-error cluster_assumption.tex
pdflatex -interaction=nonstopmode -halt-on-error cluster_assumption.tex
```

The simulator uses Python 3.11+ and the standard library. Analysis and figure generation use NumPy, pandas and Matplotlib. The checked-in tables and figures support a direct LaTeX build. The study records 820,224 capped policy runs across its three simulation arms. Exact enumerations are additional. For a quick variable-size smoke test, set `--variable-replicates 1` and choose a separate output directory.
