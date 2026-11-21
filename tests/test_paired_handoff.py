import csv
import gzip
from pathlib import Path
from random import Random
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from benchmark_paired_handoff import PairedHits, calibrate, paired_interval, run_arm
from cluster_landscapes import KeyGrid, Relabeling, key_run_lengths, relabel_energies


class PairedHandoffTests(unittest.TestCase):
    def test_matched_solid_and_isolated_targets(self):
        values = (11, 9, 0, 8, -1, 7, -2, 6, 5, 4, 3, 2)
        for seed in range(12):
            solid, isolated = relabel_energies(values, 0, Random(seed), control="isolated")
            self.assertEqual(key_run_lengths(solid.valid), (3,))
            self.assertEqual(key_run_lengths(isolated.valid), (1, 1, 1))
            for layout in (solid, isolated):
                self.assertEqual(sorted(layout.values), sorted(values))
                self.assertEqual(layout.values[0], values[0])
                self.assertEqual(layout.valid, {k for k, e in enumerate(layout.values) if e <= 0})
            self.assertEqual([solid.values[k] for k in sorted(solid.valid)],
                             [isolated.values[k] for k in sorted(isolated.valid)])

    def test_both_starters_find_a_first_hit_only_after_the_handoff(self):
        grid = KeyGrid(4)
        scores = [9.0] * grid.size
        # Separate pilot incumbents. The recursive pilot's four step-4 neighbors
        # have already been sampled, so its first new step-2 point is call 21.
        for g, b in ((8, 0), (5, 3)):
            scores[grid.key[g][b]] = 2.0
        valid = frozenset((grid.key[10][0], grid.key[9][3]))
        for key in valid:
            scores[key] = 0.0
        layout = Relabeling(tuple(scores), valid)
        for starter, winner, first_poll, first_hit in (
                ("recursive", (8, 0), (12, 0), 21), ("random", (5, 3), (9, 3), 17)):
            arm = run_arm(grid, layout, starter, 16, 21, 7)
            self.assertEqual((arm.pilot_calls, arm.local_calls), (16, 5))
            self.assertEqual(arm.handoff_key, grid.key[winner[0]][winner[1]])
            self.assertEqual(arm.first_poll_key, grid.key[first_poll[0]][first_poll[1]])
            self.assertEqual(arm.first_hit, first_hit)

    def test_calibration_penalizes_misses_and_uses_only_recursive_hits(self):
        # Missing by B=24 scores 25. The mean loss for k=16 is 13, versus 12
        # for each neighbor. Equal distance from 16 resolves to the shorter one.
        groups = {(k, label): [PairedHits("s", "a", rec, rand)]
                  for k, recs, rand in ((12, (12, 12), None), (16, (1, None), 1),
                                        (20, (12, 12), 2))
                  for label, rec in zip(("solid", "isolated"), recs)}
        with TemporaryDirectory() as tmp:
            self.assertEqual(calibrate(groups, (12, 16, 20), 16, 24, Path(tmp)), 12)
            groups[16, "isolated"] = [PairedHits("s", "a", 23, 1)]
            self.assertEqual(calibrate(groups, (12, 16, 20), 16, 24, Path(tmp)), 16)
        rows = [PairedHits("s", "a", 3, 4), PairedHits("s", "b", 5, 6)]
        self.assertEqual(paired_interval(rows, 24, 0), (-1, -1))
        self.assertEqual(paired_interval(rows[:1], 24, 0), (None, None))

    def test_small_cli_run_reconciles_raw_hits_stages_and_curves(self):
        with TemporaryDirectory() as tmp:
            out = Path(tmp)
            subprocess.run([sys.executable, str(ROOT / "examples/benchmark_paired_handoff.py"),
                            "--graphs-per-split", "1", "--draws", "1", "--out", tmp],
                           check=True, capture_output=True, timeout=30)
            with gzip.open(out / "runs.csv.gz", "rt") as stream:
                raw = list(csv.DictReader(stream))
            with (out / "comparison.csv").open() as stream:
                comparison = list(csv.DictReader(stream))
            with (out / "hit_curve.csv").open() as stream:
                curves = list(csv.DictReader(stream))
            with (out / "calibration.csv").open() as stream:
                selected, = [r["pilot"] for r in csv.DictReader(stream) if r["selected"] == "1"]
            evaluated = [r for r in raw if r["phase"] == "evaluation"]
            self.assertEqual({r["pilot"] for r in evaluated}, {"16", selected})
            self.assertTrue({r["graph"] for r in raw if r["phase"] == "calibration"}.isdisjoint(
                            r["graph"] for r in evaluated))
            for summary in comparison:
                k, layout = summary["pilot"], summary["layout"]
                pairs = [r for r in evaluated if (r["pilot"], r["layout"]) == (k, layout)]
                self.assertEqual(len(pairs), int(summary["pairs"]))
                curve = [r for r in curves if (r["pilot"], r["layout"]) == (k, layout)]
                self.assertEqual(len(curve), 65)
                for method in ("recursive", "random"):
                    hits = [int(r[f"{method}_first_hit"]) for r in pairs if r[f"{method}_first_hit"]]
                    pilot_hits = sum(t <= int(k) for t in hits)
                    self.assertEqual(int(summary[f"{method}_pilot_hits"]), pilot_hits)
                    self.assertEqual(int(summary[f"{method}_local_hits"]), len(hits) - pilot_hits)
                    self.assertEqual(int(summary[f"{method}_misses"]), len(pairs) - len(hits))
                    self.assertEqual([float(r[f"{method}_hit_rate"]) for r in curve],
                                     [sum(hit <= t for hit in hits) / len(pairs) for t in range(1, 66)])
