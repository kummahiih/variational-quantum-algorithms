"""Reproduce the hybrid comparison. Run from any directory, with Python 3.11+."""

import argparse
import csv
import gzip
import io
import json
import sys
from collections import defaultdict
from statistics import mean
from math import pi
from pathlib import Path
from random import Random

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hybrid_qaoa import CheckpointSwitch, STARTERS, search_grid
from pattern_search import ENERGY_TOLERANCE
from qaoa_benchmark import CASES, GraphCase
from sieve_qaoa import qaoa_energy

STARTS_16 = {"default": (2, 1), "flat_beta": (1, 2), "shifted": (3, 3)}
PILOT_SIZES = (*range(1, 27), 33, 49, 65)
RANDOM_SEEDS = 12
FIELDS = ("split", "case", "stratum", "bits", "budget", "start", "starter", "seed",
          "policy", "pilot_calls", "used_calls", "first_hit", "initial_energy",
          "grid_min", "target", "energy_at_20", "final_energy", "fresh_at_8")


def connected(n: int, edges: tuple[tuple[int, int], ...]) -> bool:
    neighbors = [set() for _ in range(n)]
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    reached = {0}
    stack = [0]
    while stack:
        for v in neighbors[stack.pop()]:
            if v not in reached:
                stack.append(v)
                reached.add(v)
    return len(reached) == n


def study_graphs():
    for case in CASES:
        yield "legacy", case, "legacy", None, None
    for split, seed_base in (("holdout", 17000), ("confirmation", 27000)):
        for n in (7, 8, 9):
            for level, probability in enumerate((0.35, 0.60)):
                stratum = f"n{n}_p{int(100 * probability)}"
                for replicate in range(4):
                    seed = seed_base + 100 * n + 10 * level + replicate
                    rng = Random(seed)
                    while True:
                        edges = tuple((i, j) for i in range(n) for j in range(i + 1, n)
                                      if rng.random() < probability)
                        if connected(n, edges):
                            break
                    name = f"{stratum}_r{replicate}" if split == "holdout" else f"c_{stratum}_r{replicate}"
                    yield split, GraphCase(name, n, edges), stratum, seed, replicate


def exact_landscape(case: GraphCase, bits: int):
    costs = case.costs()
    size = 1 << bits
    step = 2 * pi / size
    return [[qaoa_energy(costs, g * step, b * step) for b in range(size)]
            for g in range(size)]


def policies(budget: int, full_sweep: bool):
    sizes = PILOT_SIZES if full_sweep else (1, round(0.2 * budget), budget)
    for k in sizes:
        yield f"k{k}", k / budget, None
    yield "patience4", 0.4, 4


def run_case(writer, split, case, stratum, bits, budget, table, schedules, rules=None,
             calibration=None):
    reference = min(map(min, table))
    count = 0
    for name, base in STARTS_16.items():
        initial = tuple(x * ((1 << bits) // 16) for x in base)
        baseline = table[initial[0]][initial[1]]
        target = baseline - 0.8 * (baseline - reference)
        for policy, fraction, patience in schedules:
            # k1 has one common trace, independent of starter and seed.
            starters = ("pattern",) if policy == "k1" else STARTERS
            for starter in starters:
                seeds = range(RANDOM_SEEDS) if starter == "random" else range(1)
                for seed in seeds:
                    trace = search_grid(lambda g, b: table[g][b], angle_bits=bits,
                        max_evaluations=budget, initial=initial,
                        starter="original" if starter == "pattern" else starter,
                        pilot_fraction=fraction, patience=patience, seed=seed,
                        switch_when=rules[starter] if policy == "checkpoint" else None)
                    used = len(trace.trials)
                    first_hit = trace.first_hit(target)
                    fresh = None
                    if trace.pilot_calls >= 8:
                        fresh = trace.trials[7].best_energy < trace.trials[3].best_energy - ENERGY_TOLERANCE
                    if calibration is not None and policy in ("k8", "k13"):
                        calibration[starter, fresh, policy].append(first_hit or budget + 1)
                    writer.writerow((split, case.name, stratum, bits, budget, name, starter,
                        seed, policy, trace.pilot_calls, used, first_hit,
                        repr(baseline), repr(reference), repr(target),
                        repr(trace.trials[min(20, used)-1].best_energy), repr(trace.best_energy),
                        int(fresh) if fresh is not None else ""))
                    count += 1
    return count


def fit_rules(samples, out):
    """Both counterfactual actions share the first eight pilot calls and seeds."""
    rules = {}
    with (out / "checkpoint_rules.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(("starter", "state", "pairs", "loss_switch8", "loss_switch13", "action"))
        for starter in STARTERS:
            actions = {}
            for fresh in (False, True):
                short = samples[starter, fresh, "k8"]
                long = samples[starter, fresh, "k13"]
                n = len(short)
                if not n:  # Unseen state: pool the two states within this starter.
                    short = samples[starter, not fresh, "k8"]
                    long = samples[starter, not fresh, "k13"]
                actions[fresh] = mean(short) <= mean(long)
                writer.writerow((starter, "improving" if fresh else "stale", n,
                    mean(short), mean(long), 8 if actions[fresh] else 13))
            rules[starter] = CheckpointSwitch(actions[True], actions[False])
    return rules


def historical_curves(out: Path) -> None:
    with (ROOT / "paper/results/qaoa_benchmark_raw.csv").open(newline="") as stream:
        old = list(csv.DictReader(stream))
    with (out / "historical_crossover.csv").open("w", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        methods = ("original", "recursive", "pattern")
        writer.writerow(("evaluation", *methods))
        for t in range(1, 66):
            writer.writerow((t, *(sum(bool(r["first_hit"]) and int(r["first_hit"]) <= t
                for r in old if r["method"] == m) for m in methods)))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "paper/hybrid/results")
    args = parser.parse_args()
    out = args.out
    out.mkdir(parents=True, exist_ok=True)
    historical_curves(out)
    count = 0
    graphs = []
    calibration = defaultdict(list)
    rules = None
    # Each logical request is charged. Cross-run table reuse only accelerates replay.
    with (out / "runs.csv.gz").open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb",
        filename="", mtime=0) as compressed, io.TextIOWrapper(compressed, newline="",
        encoding="utf-8") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(FIELDS)
        for split, case, stratum, seed, rep in study_graphs():
            graphs.append(dict(case=case.name, split=split, stratum=stratum, vertices=case.n_qubits,
                               seed=seed, edges=case.edges))
            table = exact_landscape(case, 4)
            if split == "legacy":
                count += run_case(writer, split, case, stratum, 4, 65, table,
                                  list(policies(65, True)), calibration=calibration)
                continue
            if rules is None:
                rules = fit_rules(calibration, out)
            decision = ("checkpoint", 0.2, None)
            if split == "confirmation":
                settings = [(f"k{k}", k/65, None) for k in (1, 8, 13, 33, 65)]
                settings += [("patience4", 0.4, 4), decision]
                count += run_case(writer, split, case, stratum, 4, 65, table, settings, rules)
                continue
            settings = [*policies(65, True), decision]
            count += run_case(writer, split, case, stratum, 4, 65, table, settings, rules)
            count += run_case(writer, "short", case, stratum, 4, 33, table, list(policies(33, False)))
            if rep == 0:
                fine = exact_landscape(case, 5)
                count += run_case(writer, "fine", case, stratum, 5, 65, fine, list(policies(65, False)))
    (out / "graphs.json").write_text(json.dumps(graphs, indent=2) + "\n", encoding="utf-8")
    print(f"{count} policy runs, {len(graphs)} distinct graph instances. Results in {out}")


if __name__ == "__main__":
    main()
