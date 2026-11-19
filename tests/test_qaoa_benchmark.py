"""Tests for fair, deterministic exact-statevector optimizer comparisons."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from qaoa_benchmark import (
    CASES, METHODS, grid_reference, optimize_trace, run_suite,
)
from sieve_qaoa import maxcut_costs, optimize_with_recursive_sieve, qaoa_energy


class QAOABenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.costs = maxcut_costs(4, ((0, 1), (1, 2), (2, 3), (3, 0)))

    def test_methods_respect_budget_and_are_monotonic(self):
        for method in METHODS:
            for budget in (1, 5, 20, 65):
                with self.subTest(method=method, budget=budget):
                    trace = optimize_trace(self.costs, method, max_evaluations=budget)
                    self.assertGreaterEqual(trace.evaluations, 1)
                    self.assertLessEqual(trace.evaluations, budget)
                    self.assertEqual(trace.observations[0].evaluations, 1)
                    for i, point in enumerate(trace.observations, 1):
                        self.assertEqual(point.evaluations, i)
                        self.assertAlmostEqual(point.best_energy,
                            qaoa_energy(self.costs, point.gamma, point.beta), places=10)
                        self.assertTrue(0 <= point.optimal_probability <= 1 + 1e-12)
                        if i > 1:
                            self.assertLessEqual(point.best_energy,
                                trace.observations[i-2].best_energy + 1e-12)

    def test_recursive_trace_matches_original_optimizer_at_all_checkpoints(self):
        for case in CASES:
            values = case.costs()
            for initial_angles in ((math.pi/4, math.pi/8),
                                   (math.pi/8, math.pi/4),
                                   (3*math.pi/8, 3*math.pi/8)):
                for budget in (1, 2, 5, 7, 16, 17, 20, 32, 40, 65):
                    with self.subTest(case=case.name, start=initial_angles, budget=budget):
                        actual = optimize_trace(values, "recursive",
                            max_evaluations=budget, initial_angles=initial_angles)
                        original = optimize_with_recursive_sieve(values,
                            max_evaluations=budget, initial_angles=initial_angles)
                        self.assertEqual(actual.evaluations, original.evaluations)
                        self.assertAlmostEqual(actual.at_budget(budget).best_energy,
                            original.expected_energy, places=10)

    def test_order_effect_on_first_hit_in_cycle(self):
        recursive = optimize_trace(self.costs, "recursive")
        original = optimize_trace(self.costs, "original")
        self.assertEqual(recursive.first_hit(-2.9), 7)
        self.assertEqual(original.first_hit(-2.9), 6)
        self.assertAlmostEqual(recursive.at_budget(65).best_energy, -3)
        self.assertAlmostEqual(original.at_budget(65).best_energy, -3)

    def test_random_reproducibility(self):
        for method in ("shuffled", "random_joint"):
            first = optimize_trace(self.costs, method, seed=8)
            again = optimize_trace(self.costs, method, seed=8)
            other = optimize_trace(self.costs, method, seed=9)
            self.assertEqual(first, again)
            self.assertNotEqual(first, other)

    def test_trace_first_hit_and_early_completion(self):
        pattern = optimize_trace(self.costs, "pattern", max_evaluations=65)
        self.assertLessEqual(pattern.evaluations, 65)
        self.assertEqual(pattern.first_hit(-2.9), 2)
        self.assertEqual(pattern.first_hit(1), 1)
        self.assertIsNone(pattern.first_hit(-4))
        self.assertEqual(pattern.at_budget(100), pattern.observations[-1])

    def test_grid_reference_is_valid_and_shared(self):
        for case in CASES:
            costs = case.costs()
            ref = grid_reference(costs)
            self.assertLessEqual(ref, qaoa_energy(costs, math.pi/4, math.pi/8) + 1e-12)
        self.assertAlmostEqual(grid_reference(self.costs), -3, places=10)

    def test_suite_has_expected_rows_and_targets(self):
        rows = run_suite(random_seeds=3)
        self.assertEqual(len(rows), len(CASES)*3*(4+2*3))
        for r in rows:
            self.assertLessEqual(r.grid_reference_energy, r.target_energy)
            self.assertLess(r.target_energy, r.initial_energy)
            self.assertLessEqual(r.used_evaluations, 65)
            self.assertTrue(r.energy_at_65 <= r.energy_at_40 + 1e-12)
            self.assertTrue(r.energy_at_40 <= r.energy_at_20 + 1e-12)
            self.assertTrue(r.energy_at_20 <= r.energy_at_10 + 1e-12)

    def test_invalid_arguments(self):
        with self.assertRaises(ValueError):
            optimize_trace(self.costs, "other")
        with self.assertRaises(ValueError):
            optimize_trace(self.costs, "recursive", max_evaluations=0)
        with self.assertRaises(ValueError):
            optimize_trace([0, 1, 2], "recursive")
        with self.assertRaises(ValueError):
            optimize_trace(self.costs, "recursive", initial_angles=(math.inf, 1))
        with self.assertRaises(ValueError):
            optimize_trace(self.costs, "recursive").at_budget(0)
        with self.assertRaises(ValueError):
            optimize_trace(self.costs, "recursive").first_hit(float('nan'))
        with self.assertRaises(ValueError):
            run_suite(target_fraction=1)


if __name__ == "__main__":
    unittest.main()
