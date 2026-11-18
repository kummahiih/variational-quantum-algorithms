"""Run with: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from dyadic_sieve import keys, vectors


class DyadicSieveTests(unittest.TestCase):
    def test_four_bits(self):
        self.assertEqual(list(keys(4)), [
            8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15, 0
        ])
        self.assertEqual(list(vectors(4))[5], [1, 0, 1, 0])

    def test_permutation(self):
        for n in range(9):
            values = list(keys(n))
            self.assertEqual(len(values), 1 << n)
            self.assertEqual(set(values), set(range(1 << n)))

    def test_negative(self):
        with self.assertRaises(ValueError):
            list(keys(-1))


if __name__ == "__main__":
    unittest.main()
