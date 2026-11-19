"""Independent finite-enumeration checks for the note (not a Lean proof)."""
from fractions import Fraction
from math import pi, sin
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "src"))
from dyadic_sieve import keys as original_keys
from recursive_dyadic_sieve import keys as recursive_keys
from sieve_qaoa import maxcut_costs, qaoa_energy


def verify_first_hits() -> int:
    tested = 0
    for order in (original_keys, recursive_keys):
        for n in range(1, 10):
            N = 1 << n
            visited = tuple(order(n))
            assert len(visited) == N and set(visited) == set(range(N))
            rank = {key: t for t, key in enumerate(visited, start=1)}
            for r in range(1, n + 1):
                m = 1 << r
                exact = Fraction(sum(
                    min(rank[k] for k in range(a, a + m))
                    for a in range(N-m+1)), N-m+1)
                formula = Fraction(N*(N-m+2), 2*m*(N-m+1))
                assert exact == formula, (order.__module__, n, m, exact, formula)
                tested += 1
    return tested


def verify_qaoa_cycle() -> float:
    costs = maxcut_costs(4, ((0, 1), (1, 2), (2, 3), (3, 0)))
    max_error = 0.0
    for g in range(16):
        for b in range(16):
            gamma, beta = 2*pi*g/16, 2*pi*b/16
            numeric = qaoa_energy(costs, gamma, beta)
            exact_form = -2 + sin(4*beta)*sin(2*gamma)
            max_error = max(max_error, abs(numeric-exact_form))
    assert max_error < 1e-12, max_error
    return max_error


if __name__ == "__main__":
    count = verify_first_hits()
    error = verify_qaoa_cycle()
    print(f"First-hit expectation: {count} verified order/width/cluster configurations")
    print(f"Four-cycle QAOA energy: 256 grid checks; maximum absolute error {error:.3g}")
