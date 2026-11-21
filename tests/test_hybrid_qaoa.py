"""Regression checks for pilot schedules, charged calls, and the local handoff."""

from math import pi
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hybrid_qaoa import CheckpointSwitch, STARTERS, optimize_hybrid, search_grid
from qaoa_benchmark import CASES, optimize_trace
from sieve_qaoa import qaoa_energy


class HybridTests(unittest.TestCase):
    def test_joint_starters_cover_the_torus_and_skip_the_initial_cell(self):
        for starter in STARTERS[:5]:
            with self.subTest(starter=starter):
                trace = search_grid(lambda x, y: x + y, starter=starter, initial=(6, 7),
                                    angle_bits=3, pilot_fraction=1, max_evaluations=100)
                self.assertEqual(trace.pilot_calls, 64)
                self.assertEqual(len(trace.trials), 64)
                self.assertEqual({t.point for t in trace.trials},
                                 {(i, j) for i in range(8) for j in range(8)})

    def test_known_sobol_and_halton_points_and_seeded_randomness(self):
        def points(starter, seed=0):
            trace = search_grid(lambda *_: 0, initial=(0, 0), starter=starter,
                                pilot_fraction=1, max_evaluations=6, seed=seed)
            return [t.point for t in trace.trials]
        self.assertEqual(points("sobol"), [(0,0),(8,8),(12,4),(4,12),(6,6),(14,14)])
        self.assertEqual(points("halton"), [(0,0),(8,5),(4,10),(12,1),(2,7),(10,12)])
        self.assertEqual(points("random", 3), points("random", 3))
        self.assertNotEqual(points("random", 3), points("random", 4))
        self.assertNotEqual(points("original"), points("recursive"))

    def test_legacy_patterns_and_coordinate_prefixes(self):
        for case in CASES:
            costs = case.costs()
            for initial in ((2, 1), (1, 2), (3, 3)):
                for method in ("pattern", "original", "recursive"):
                    with self.subTest(case=case.name, initial=initial, method=method):
                        prior = optimize_trace(costs, method, initial_angles=tuple(v*pi/8 for v in initial))
                        hybrid = optimize_hybrid(costs, initial=initial,
                            starter="recursive" if method == "pattern" else method+"_coordinate",
                            pilot_fraction=0 if method == "pattern" else 1)
                        self.assertEqual(len(prior.observations), len(hybrid.trials))
                        for old, new in zip(prior.observations, hybrid.trials):
                            self.assertAlmostEqual(old.best_energy, new.best_energy, places=10)
                            self.assertEqual(tuple(round(v/(pi/8)) % 16 for v in (old.gamma, old.beta)),
                                             new.incumbent)

    def test_handoff_charges_each_request_and_reuses_winning_pilot(self):
        calls = []
        def objective(x, y):
            calls.append((x, y))
            return float(-x-y)
        trace = search_grid(objective, max_evaluations=12, pilot_fraction=0.5, initial=(0, 0))
        self.assertEqual(calls, [t.point for t in trace.trials])
        self.assertEqual(len(calls), 12)
        self.assertEqual(trace.pilot_calls, 6)
        g, b = trace.trials[5].incumbent
        self.assertEqual(calls[6:10], [((g+4)%16,b), ((g-4)%16,b),
                                       (g,(b+4)%16), (g,(b-4)%16)])
        self.assertEqual(trace.first_hit(trace.trials[0].energy), 1)
        self.assertIsNone(trace.first_hit(-1000))

    def test_patience_uses_observed_improvements_and_enforces_its_cap(self):
        flat = search_grid(lambda *_: 1, initial=(0,0), starter="recursive",
                           pilot_fraction=0.4, patience=4)
        self.assertEqual(flat.pilot_calls, 5)
        self.assertLess(len(flat.trials), 65)
        self.assertLess(len({t.point for t in flat.trials}), len(flat.trials))
        calls = 0
        def improving(*_):
            nonlocal calls
            calls += 1
            return -calls
        self.assertEqual(search_grid(improving, pilot_fraction=0.4, patience=4).pilot_calls, 26)
        tiny = search_grid(lambda *_: 0, max_evaluations=1, patience=4)
        self.assertEqual(len(tiny.trials), 1)
        for calls in (2, 5, 13, 14, 19):
            trace = search_grid(lambda x,y: x+y, max_evaluations=calls, pilot_fraction=0.2)
            self.assertLessEqual(len(trace.trials), calls)
            self.assertEqual(trace.pilot_calls, max(1, int(0.2*calls+0.5)))

    def test_statevector_wrapper_matches_table_replay_on_every_candidate(self):
        costs = CASES[-1].costs()
        step = 2*pi / 16
        table = [[qaoa_energy(costs, x*step, y*step) for y in range(16)] for x in range(16)]
        for starter in STARTERS:
            for patience in (None, 4):
                options = dict(starter=starter, pilot_fraction=0.2, patience=patience, seed=9)
                live = optimize_hybrid(costs, **options)
                replay = search_grid(lambda x,y: table[x][y], **options)
                self.assertEqual(live, replay)
                self.assertAlmostEqual(live.best_energy, qaoa_energy(costs, *live.best_angles))

    def test_checkpoint_rule_branches_only_on_history(self):
        options = dict(max_evaluations=65, pilot_fraction=0.2,
                       switch_when=CheckpointSwitch(switch_if_improving=False, switch_if_stale=True))
        self.assertEqual(search_grid(lambda *_: 1, **options).pilot_calls, 8)
        for starter in STARTERS:
            costs = CASES[1].costs()
            dynamic = optimize_hybrid(costs, starter=starter, **options)
            fresh = dynamic.trials[7].best_energy < dynamic.trials[3].best_energy - 1e-12
            expected = 13 if fresh else 8
            fixed = optimize_hybrid(costs, starter=starter, pilot_fraction=expected/65)
            self.assertEqual(dynamic, fixed)
        once = search_grid(lambda *_: 0, pilot_fraction=1,
                           switch_when=lambda history: len(history) == 1)
        self.assertEqual(once.pilot_calls, 1)
        self.assertGreater(len(once.trials), 1)

    def test_maxcut_beta_symmetry_reduces_joint_dyadic_prefix(self):
        costs = CASES[-1].costs()
        initial = (3, 3)
        for starter, expected_pairs in (("original", 4), ("recursive", 4), ("halton", 13)):
            trace = optimize_hybrid(costs, starter=starter, initial=initial)
            classes = {(trial.point[0], trial.point[1] % 4) for trial in trace.trials[:13]}
            self.assertEqual(len(classes), expected_pairs)
            for trial in trace.trials[:13]:
                g, b = trial.point
                equivalent = qaoa_energy(costs, g*pi/8, (b % 4)*pi/8)
                self.assertAlmostEqual(trial.energy, equivalent, places=10)

    def test_validation_and_small_grids(self):
        for options in (dict(angle_bits=0), dict(max_evaluations=0), dict(initial=(16,0)),
                        dict(starter="bad"), dict(patience=0), dict(pilot_fraction=-0.1)):
            with self.assertRaises(ValueError):
                search_grid(lambda *_: 0, **options)
        with self.assertRaises(ValueError):
            search_grid(lambda *_: float("nan"))
        trace = search_grid(lambda *_: 0, angle_bits=1, pilot_fraction=0)
        self.assertEqual(len(trace.trials), 1)


if __name__ == "__main__":
    unittest.main()
