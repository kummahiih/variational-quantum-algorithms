import Lean

/-
  A finite, uniform distribution over cluster start positions.

  For N keys and a solid cluster of length m, there are N-m+1
  possible starts. The exact expected first-hit time is the
  sum of the first-hit times divided by N-m+1.

  The statements below prove finite-sum consequences for any
  first-hit function. They do NOT yet derive a closed-form formula
  for the dyadic sieve or establish its comparison to random sampling.
-/

def clusterTrialSum (positions : Nat) (firstHit : Nat → Nat) : Nat :=
  ∑ start ∈ Finset.range positions, firstHit start

-- If every cluster position is discovered within B trials,
-- the total first-hit time is at most positions * B.
theorem clusterTrialSum_le (positions bound : Nat)
    (firstHit : Nat → Nat)
    (hbound : ∀ start < positions, firstHit start ≤ bound) :
    clusterTrialSum positions firstHit ≤ positions * bound := by
  unfold clusterTrialSum
  calc
    (∑ start ∈ Finset.range positions, firstHit start)
        ≤ ∑ _start ∈ Finset.range positions, bound := by
            apply Finset.sum_le_sum
            intro start hmem
            exact hbound start (Finset.mem_range.mp hmem)
    _ = positions * bound := by simp

-- The numerator comparison needed for comparing two uniform averages.
-- The rational-valued expectation is this sum divided by positions.
theorem clusterTrialSum_compare (positions : Nat)
    (sieveHit otherHit : Nat → Nat)
    (h : ∀ start < positions, sieveHit start ≤ otherHit start) :
    clusterTrialSum positions sieveHit ≤
      clusterTrialSum positions otherHit := by
  unfold clusterTrialSum
  apply Finset.sum_le_sum
  intro start hmem
  exact h start (Finset.mem_range.mp hmem)
