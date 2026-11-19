"""Run with: python -m unittest discover -s tests -v"""
import sys
import unittest
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dyadic_sieve import keys as ascending_keys
from recursive_dyadic_sieve import keys, vectors


class RecursiveDyadicSieveTests(unittest.TestCase):
    def test_four_bits(self):
        self.assertEqual(list(keys(4)), [
            8, 4, 12, 2, 10, 6, 14, 1, 9, 5, 13, 3, 11, 7, 15, 0
        ])
        self.assertEqual(list(vectors(4))[5], [0, 1, 1, 0])

    def test_permutation(self):
        for n in range(9):
            values = list(keys(n))
            self.assertEqual(len(values), 1 << n)
            self.assertEqual(set(values), set(range(1 << n)))
            self.assertEqual(values[-1], 0)

    def test_level_membership_matches_original(self):
        for n in range(9):
            original = list(ascending_keys(n))
            recursive = list(keys(n))
            offset = 0
            for level in range(n):
                count = 1 << level
                self.assertEqual(
                    set(original[offset:offset + count]),
                    set(recursive[offset:offset + count]),
                )
                offset += count

    def test_non_solid_hit_order_changes(self):
        original = list(ascending_keys(4))
        recursive = list(keys(4))
        def first_hit(order, successful):
            return next(t for t, key in enumerate(order, 1) if key in successful)
        self.assertEqual(first_hit(original, {6, 14}), 5)
        self.assertEqual(first_hit(recursive, {6, 14}), 6)
        self.assertEqual(first_hit(original, {10, 14}), 6)
        self.assertEqual(first_hit(recursive, {10, 14}), 5)

    def test_power_of_two_solid_cluster_expectation(self):
        # Changing the order within a complete level does not change
        # the uniform-start average for power-of-two solid clusters.
        for n in range(1, 8):
            size = 1 << n
            rank = {key: trial for trial, key in enumerate(keys(n), 1)}
            for r in range(1, n + 1):
                m = 1 << r
                total = sum(
                    min(rank[key] for key in range(start, start + m))
                    for start in range(size - m + 1)
                )
                self.assertEqual(
                    Fraction(total, size - m + 1),
                    Fraction(size * (size - m + 2),
                             2 * m * (size - m + 1)),
                )

    def test_negative(self):
        with self.assertRaises(ValueError):
            list(keys(-1))
        with self.assertRaises(ValueError):
            list(vectors(-1))


if __name__ == "__main__":
    unittest.main()
