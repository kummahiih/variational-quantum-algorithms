"""Run from the repository root: python examples/sieve_qaoa_maxcut.py"""
import sys
from math import pi
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from sieve_qaoa import maxcut_costs, optimize_with_recursive_sieve, qaoa_energy


def main() -> None:
    # Four vertices on a cycle; minimize negative cut size.
    costs = maxcut_costs(4, [(0, 1), (1, 2), (2, 3), (3, 0)])
    baseline = qaoa_energy(costs, pi / 4, pi / 8)
    result = optimize_with_recursive_sieve(costs, angle_bits=4, sweeps=2)
    print(f"initial expected energy: {baseline:.6f}")
    print(f"optimized expected energy: {result.expected_energy:.6f}")
    print(f"gamma={result.gamma:.6f}, beta={result.beta:.6f}")
    print(f"exact statevector evaluations: {result.evaluations}")
    print(f"most likely bitstring: {result.most_likely_bitstring}")
    print("top outcomes:")
    for x in sorted(range(len(costs)), key=lambda i: result.probabilities[i], reverse=True)[:4]:
        print(f"  {x:04b}: probability={result.probabilities[x]:.3f}, cost={costs[x]:g}")
    print("Note: this is an ideal statevector simulation, not a hardware benchmark.")


if __name__ == "__main__":
    main()
