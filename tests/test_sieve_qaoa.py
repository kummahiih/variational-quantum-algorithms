"""Run with: python -m unittest discover -s tests -v"""
import math
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sieve_qaoa import (
    maxcut_costs, optimize_with_recursive_sieve, qaoa_energy,
    qaoa_probabilities,
)
from recursive_dyadic_sieve import keys as recursive_keys


class SieveQAOATests(unittest.TestCase):
    def setUp(self):
        self.costs = maxcut_costs(4, [(0, 1), (1, 2), (2, 3), (3, 0)])

    def test_binary_costs(self):
        self.assertEqual(maxcut_costs(2, [(0, 1)]), (0., -1., -1., 0.))
        self.assertEqual(self.costs[0b0101], -4.)
        self.assertEqual(self.costs[0b1010], -4.)

    def test_unitary_probabilities(self):
        for gamma, beta in [(0, 0), (math.pi / 4, math.pi / 8), (1.5, 2.4)]:
            probs = qaoa_probabilities(self.costs, gamma, beta)
            self.assertAlmostEqual(sum(probs), 1, places=12)
            self.assertTrue(all(0 <= p <= 1 for p in probs))

    def test_zero_cost_angle_is_uniform(self):
        probs = qaoa_probabilities(self.costs, 0, 0.41)
        for p in probs:
            self.assertAlmostEqual(p, 1 / len(self.costs), places=12)

    def test_optimizer_improves(self):
        initial = qaoa_energy(self.costs, math.pi / 4, math.pi / 8)
        with patch("sieve_qaoa.recursive_keys", wraps=recursive_keys) as sieve:
            result = optimize_with_recursive_sieve(self.costs, angle_bits=4, sweeps=2)
        self.assertLess(result.expected_energy, initial)
        self.assertEqual(result.evaluations, 1 + 2 * 2 * 16)
        self.assertEqual(sieve.call_count, 4)  # one call per parameter/sweep
        self.assertEqual(len(result.most_likely_bitstring), 4)
        self.assertAlmostEqual(
            qaoa_energy(self.costs, result.gamma, result.beta),
            result.expected_energy, places=12,
        )

    def test_stop_on_energy_threshold(self):
        result = optimize_with_recursive_sieve(self.costs, target_energy=1)
        self.assertEqual(result.evaluations, 1)

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            qaoa_probabilities([0, -1, -2], .1, .2)
        with self.assertRaises(ValueError):
            qaoa_probabilities([0, float("nan")], .1, .2)
        with self.assertRaises(ValueError):
            maxcut_costs(2, [(0, 0)])
        with self.assertRaises(ValueError):
            optimize_with_recursive_sieve(self.costs, angle_bits=0)
        with self.assertRaises(ValueError):
            optimize_with_recursive_sieve(self.costs, sweeps=0)
        with self.assertRaises(ValueError):
            optimize_with_recursive_sieve(self.costs, initial_angles=(0,))


if __name__ == "__main__":
    unittest.main()
