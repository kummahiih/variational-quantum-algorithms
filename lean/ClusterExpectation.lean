import Lean

/-
  Solid-cluster first-hit expectation: elementary finite-sum lemmas.

  If a cluster of length m is uniformly located in an N-key space,
  there are N-m+1 possible starts. The expected first-hit time is
  the sum of the first-hit times divided by N-m+1.

  We use a recursive sum to avoid requiring Mathlib's big-operator
  notation. These lemmas do not establish a closed-form expectation
  for the dyadic sieve.
-/

def clusterTrialSum : Nat → (Nat → Nat) → Nat
  | 0, _ => 0
  | positions + 1, firstHit =>
      clusterTrialSum positions firstHit + firstHit positions

theorem clusterTrialSum_le (positions bound : Nat)
    (firstHit : Nat → Nat)
    (hbound : ∀ start < positions, firstHit start ≤ bound) :
    clusterTrialSum positions firstHit ≤ positions * bound := by
  induction positions with
  | zero =>
      simp [clusterTrialSum]
  | succ positions ih =>
      have hprefix : ∀ start < positions, firstHit start ≤ bound := by
        intro start hs
        exact hbound start (by omega)
      have hlast : firstHit positions ≤ bound :=
        hbound positions (by omega)
      have hsum := ih hprefix
      simp only [clusterTrialSum]
      omega

theorem clusterTrialSum_compare (positions : Nat)
    (sieveHit otherHit : Nat → Nat)
    (h : ∀ start < positions, sieveHit start ≤ otherHit start) :
    clusterTrialSum positions sieveHit ≤
      clusterTrialSum positions otherHit := by
  induction positions with
  | zero =>
      simp [clusterTrialSum]
  | succ positions ih =>
      have hprefix : ∀ start < positions, sieveHit start ≤ otherHit start := by
        intro start hs
        exact h start (by omega)
      have hlast : sieveHit positions ≤ otherHit positions :=
        h positions (by omega)
      have hsum := ih hprefix
      simp only [clusterTrialSum]
      omega
