"""Compare two global starting orders followed by identical local pattern search."""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from random import Random
from statistics import fmean, quantiles
from tempfile import TemporaryDirectory
from typing import NamedTuple

from benchmark_cluster_assumption import data_writer, seed_for
from benchmark_hybrid_qaoa import ROOT, STARTS_16, exact_landscape
from cluster_landscapes import KeyGrid, key_run_lengths, relabel_energies
from hybrid_qaoa import search_grid
from qaoa_benchmark import GraphCase

LAYOUTS = ("solid", "isolated")
STARTERS = ("recursive", "random")


class Arm(NamedTuple):
    pilot_calls: int
    handoff_key: int
    handoff_energy: float
    first_poll_key: int
    local_calls: int
    first_hit: int | None


class PairedHits(NamedTuple):
    stratum: str
    graph: str
    recursive: int | None
    random: int | None


def run_arm(grid, layout, starter, pilot, budget, order_seed):
    """Only the scalar energy is visible to the optimizer. Score target hits offline."""
    trace = search_grid(lambda g, b: layout.values[grid.key[g][b]],
                        angle_bits=grid.bits, initial=(0, 0), starter=starter,
                        pilot_fraction=pilot / budget, max_evaluations=budget, seed=order_seed)
    paid = trace.pilot_calls
    if paid != pilot or paid >= len(trace.trials):
        raise AssertionError("expected the full pilot and at least one local poll")
    g, b = trace.trials[paid-1].incumbent
    pg, pb = trace.trials[paid].point
    hit = next((t for t, trial in enumerate(trace.trials, 1)
                if grid.key[trial.point[0]][trial.point[1]] in layout.valid), None)
    return Arm(paid, grid.key[g][b], trace.trials[paid-1].best_energy, grid.key[pg][pb],
               len(trace.trials) - paid, hit)


def run_cohort(phase, graphs, pilots, args, writer):
    grid = KeyGrid(4)
    groups = defaultdict(list)
    for index, graph in enumerate(graphs, 1):
        case = GraphCase(graph["case"], graph["vertices"], tuple(map(tuple, graph["edges"])))
        table = exact_landscape(case, grid.bits)
        minimum = min(map(min, table))
        for start, (g0, b0) in STARTS_16.items():
            values = tuple(table[(g0+g) % grid.side][(b0+b) % grid.side] for g, b in grid.points)
            target = values[0] - 0.8 * (values[0] - minimum)
            for draw in range(args.draws):
                coordinates = (args.seed, phase, case.name, start, draw)
                layout_seed = seed_for("paired-handoff-layout-v1", *coordinates)
                order_seed = seed_for("paired-handoff-order-v1", *coordinates)
                layouts = relabel_energies(values, target, Random(layout_seed), control="isolated")
                for label, layout in zip(LAYOUTS, layouts):
                    runs = key_run_lengths(layout.valid)
                    for pilot in pilots:
                        recursive, random = (run_arm(grid, layout, starter, pilot, args.budget,
                                                     order_seed) for starter in STARTERS)
                        writer.writerow((phase, graph["stratum"], case.name, start, draw, label,
                                         args.seed, layout_seed, order_seed, len(layout.valid),
                                         len(runs), max(runs), values[0], target, args.budget, pilot,
                                         *recursive, *random))
                        groups[pilot, label].append(PairedHits(graph["stratum"], case.name,
                                                               recursive.first_hit, random.first_hit))
        print(f"{phase} {index}/{len(graphs)} complete ({case.name})", flush=True)
    return groups


def loss(hit, budget):
    return budget + 1 if hit is None else hit


def calibrate(groups, pilots, primary, budget, out):
    # Every candidate has the same number of paired cases in each layout.
    totals = {k: [sum(loss(r.recursive, budget) for r in groups[k, label]) for label in LAYOUTS]
              for k in pilots}
    chosen = min(pilots, key=lambda k: (sum(totals[k]), abs(k-primary), k))
    with data_writer(out / "calibration.csv", ("pilot", "pairs_per_layout", "solid_mean_loss",
                     "isolated_mean_loss", "pooled_mean_loss", "selected")) as writer:
        for k in pilots:
            n = len(groups[k, "solid"])
            solid, isolated = totals[k]
            writer.writerow((k, n, solid/n, isolated/n, (solid+isolated)/(2*n), int(k == chosen)))
    return chosen


def paired_interval(rows, budget, seed):
    """Resample whole graph differences within the archived size/density strata."""
    by_graph = defaultdict(list)
    for row in rows:
        by_graph[row.stratum, row.graph].append(loss(row.recursive, budget) - loss(row.random, budget))
    strata = defaultdict(list)
    for (stratum, _), differences in by_graph.items():
        strata[stratum].append(fmean(differences))
    if any(len(graphs) < 2 for graphs in strata.values()):
        return None, None
    rng = Random(seed)
    means = [sum(sum(rng.choices(graphs, k=len(graphs))) for graphs in strata.values()) / len(by_graph)
             for _ in range(2000)]
    cuts = quantiles(means, n=40, method="inclusive")
    return cuts[0], cuts[-1]


def summarize(groups, primary, chosen, budget, seed, out):
    arm_fields = ("pilot_hits", "local_hits", "misses", "mean_loss")
    fields = ("pilot", "primary", "selected", "layout", "graphs", "pairs",
              *(f"{s}_{f}" for s in STARTERS for f in arm_fields),
              "delta_mean_calls", "ci95_low", "ci95_high")
    with data_writer(out / "comparison.csv", fields) as summary, data_writer(
            out / "hit_curve.csv", ("pilot", "layout", "call", "pairs", "recursive_hit_rate",
                                    "random_hit_rate")) as curves:
        for (pilot, label), rows in sorted(groups.items()):
            n = len(rows)
            hits = [Counter(r.recursive for r in rows), Counter(r.random for r in rows)]
            stats = []
            for hist in hits:
                pilot_hits = sum(count for t, count in hist.items() if t is not None and t <= pilot)
                avg = sum(loss(t, budget) * count for t, count in hist.items()) / n
                stats.append((pilot_hits, n - hist[None] - pilot_hits, hist[None], avg))
            delta = stats[0][-1] - stats[1][-1]
            summary.writerow((pilot, int(pilot == primary), int(pilot == chosen), label,
                              len({r.graph for r in rows}), n, *stats[0], *stats[1], delta,
                              *paired_interval(rows, budget, seed)))
            print(f"{label}, {pilot}-call start — recursive hit {n-hits[0][None]}/{n}, "
                  f"random hit {n-hits[1][None]}/{n}, paired difference {delta:+.2f} calls",
                  flush=True)
            rec_hits = rand_hits = 0
            for t in range(1, budget + 1):
                rec_hits += hits[0][t]
                rand_hits += hits[1][t]
                curves.writerow((pilot, label, t, n, rec_hits/n, rand_hits/n))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "paper/handoff/results")
    parser.add_argument("--budget", type=int, default=65, help="total paid calls per run")
    parser.add_argument("--primary", type=int, default=16, help="fixed comparison, also calibrated")
    parser.add_argument("--pilots", type=int, nargs="+", default=[12, 14, 16, 18, 20],
                        help="candidate pilot lengths including the paid initial point")
    parser.add_argument("--draws", type=int, default=32, help="paired placements per graph/start")
    parser.add_argument("--graphs-per-split", type=int, default=24, help="use the first 1–24 graphs")
    parser.add_argument("--seed", type=int, default=20261121)
    args = parser.parse_args()
    pilots = sorted({args.primary, *args.pilots})
    if pilots[0] < 1 or pilots[-1] > 256 or pilots[-1] >= args.budget:
        parser.error("each pilot must be in 1..256 and leave at least one call for polling")
    if args.draws < 1 or not 1 <= args.graphs_per_split <= 24:
        parser.error("draws must be positive and graphs-per-split must be in 1..24")

    archive = json.loads((ROOT / "paper/hybrid/results/graphs.json").read_text(encoding="utf-8"))
    calibration = [g for g in archive if g["split"] == "holdout"][:args.graphs_per_split]
    evaluation = [g for g in archive if g["split"] == "confirmation"][:args.graphs_per_split]
    fields = ("phase", "stratum", "graph", "start", "draw", "layout", "seed", "layout_seed",
              "order_seed", "valid_count", "key_runs", "longest_run", "initial_energy", "target",
              "budget", "pilot", *(f"{s}_{f}" for s in STARTERS for f in Arm._fields))
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"{len(calibration)} calibration + {len(evaluation)} evaluation graphs, "
          f"draws per start {args.draws}, pilot lengths {pilots}, budget {args.budget}", flush=True)
    # Publish completed files only. An interrupted simulation can be rerun in the same directory.
    with TemporaryDirectory(dir=args.out) as tmp:
        out = Path(tmp)
        with data_writer(out / "runs.csv.gz", fields) as writer:
            groups = run_cohort("calibration", calibration, pilots, args, writer)
            chosen = calibrate(groups, pilots, args.primary, args.budget, out)
            print(f"Calibration chose {chosen} calls. Fixed comparison uses {args.primary}.", flush=True)
            groups = run_cohort("evaluation", evaluation, sorted({args.primary, chosen}), args, writer)
        summarize(groups, args.primary, chosen, args.budget, args.seed, out)
        for path in out.iterdir():
            path.replace(args.out / path.name)
    print(f"Complete. Paired results in {args.out}", flush=True)


if __name__ == "__main__":
    main()
