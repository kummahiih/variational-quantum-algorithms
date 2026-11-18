import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cluster_expectation import (
    expected_first_hit,
    power_of_two_cluster_expectation,
    power_of_two_cluster_sum,
    first_hit_times,
    random_with_replacement_expectation,
    random_without_replacement_expectation,
)


class ClusterExpectationTests(unittest.TestCase):
    def test_exact_small_cases(self):
        self.assertEqual(expected_first_hit(4, 1), Fraction(17, 2))
        self.assertEqual(expected_first_hit(4, 2), Fraction(64, 15))
        self.assertEqual(expected_first_hit(4, 3), Fraction(22, 7))
        self.assertEqual(expected_first_hit(4, 16), Fraction(1))

    def test_first_hit_matches_direct_scan(self):
        from dyadic_sieve import keys
        for n in range(6):
            order = list(keys(n))
            for m in range(1, (1 << n) + 1):
                expected = [
                    next(t for t, key in enumerate(order, 1) if start <= key < start + m)
                    for start in range((1 << n) - m + 1)
                ]
                self.assertEqual(first_hit_times(n, m), expected)

    def test_power_of_two_closed_form(self):
        for n in range(10):
            size = 1 << n
            for r in range(n + 1):
                length = 1 << r
                exact = expected_first_hit(n, length)
                self.assertEqual(power_of_two_cluster_expectation(n, length), exact)
                self.assertEqual(
                    power_of_two_cluster_sum(n, length),
                    sum(first_hit_times(n, length)),
                )
                if 1 < length < size:
                    self.assertLess(
                        exact,
                        random_without_replacement_expectation(n, length),
                    )

    def test_random_baselines(self):
        self.assertEqual(random_with_replacement_expectation(4, 2), Fraction(8))
        self.assertEqual(random_without_replacement_expectation(4, 2), Fraction(17, 3))

    def test_invalid_cluster(self):
        with self.assertRaises(ValueError):
            expected_first_hit(4, 0)


if __name__ == "__main__":
    unittest.main()
