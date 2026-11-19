"""Run exact-statevector QAOA angle-optimizer benchmarks from repository root.

    python examples/benchmark_qaoa_optimizers.py
    python examples/benchmark_qaoa_optimizers.py --csv results.csv

No extra dependencies; only exact statevector evaluations are compared.
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from qaoa_benchmark import METHODS, run_suite


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--random-seeds", type=int, default=12,
                        help="independent shuffled/random-joint runs per case/start")
    parser.add_argument("--csv", type=Path,
                        help="write one CSV row per case/start/method/seed")
    args = parser.parse_args()
    rows = run_suite(random_seeds=args.random_seeds)
    if args.csv:
        args.csv.parent.mkdir(parents=True, exist_ok=True)
        with args.csv.open("w", newline="", encoding="utf8") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(asdict(rows[0])))
            writer.writeheader()
            writer.writerows(asdict(row) for row in rows)
        print(f"Saved {len(rows)} runs to {args.csv}")
    by_method = defaultdict(list)
    for row in rows:
        by_method[row.method].append(row)

    print("Five MaxCut graphs x three fixed starting points; angle_bits=4; budget=65")
    print("Reference: uncharged exhaustive 16x16 angle grid per graph")
    print("Target: 80% of the initial-to-grid-reference energy improvement")
    print("Best-so-far energies; exact statevector evaluations, NOT quantum shots")
    print("\nmethod        runs  hit@10  hit@20  hit@65  median first hit  mean normalized gain@10/@65  P(optimal)@65")
    for method in METHODS:
        rr = by_method[method]
        hits = [r.first_hit for r in rr if r.first_hit is not None]
        def rate(bound: int) -> str:
            return f"{sum(r.first_hit is not None and r.first_hit <= bound for r in rr) / len(rr):5.1%}"
        def gain(bound: int) -> float:
            return statistics.mean((r.initial_energy - getattr(r, f'energy_at_{bound}')) /
                                   (r.initial_energy - r.grid_reference_energy) for r in rr)
        median = f"{statistics.median(hits):5g}" if hits else "  n/a"
        optimal = statistics.mean(r.optimal_probability_at_65 for r in rr)
        print(f"{method:13} {len(rr):4d}   {rate(10):>5}   {rate(20):>5}   {rate(65):>5}       {median:>5}             {gain(10):5.1%}/{gain(65):5.1%}            {optimal:5.1%}")
    print("\nNote: pattern search may terminate before the cap; unused budget is not charged.")
    print("Stochastic methods use their seeded runs; no statistical significance claimed.")


if __name__ == "__main__":
    main()
