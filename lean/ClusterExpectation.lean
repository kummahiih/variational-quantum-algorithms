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
      rw [clusterTrialSum, Nat.succ_mul]
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


/-
  Closed-form arithmetic for solid clusters of power-of-two length.

  Put N = m*q. The midpoint sampling pattern suggests the first-hit
  histogram: m cluster starts are first hit at each trial 1,...,q-1,
  and the one remaining boundary start is hit at trial q.

  Its trial sum is m*(0+1+...+(q-1)) + q.
  The following proofs establish the resulting arithmetic formula.
  A separate proof must still derive this histogram from sieveKey.
-/

def triangular : Nat → Nat
  | 0 => 0
  | q + 1 => triangular q + q

theorem triangular_double_succ (q : Nat) :
    2 * triangular (q + 1) = q * (q + 1) := by
  induction q with
  | zero =>
      simp [triangular]
  | succ q ih =>
      rw [triangular]
      rw [Nat.mul_add] at *
      rw [Nat.succ_eq_add_one] at *
      simp only [Nat.mul_add, Nat.add_mul]
      omega

def powerTwoClusterTrialTotal (m q : Nat) : Nat :=
  m * triangular q + q

theorem powerTwoClusterTrialTotal_succ (m q : Nat) :
    powerTwoClusterTrialTotal m (q + 1) =
      powerTwoClusterTrialTotal m q + m * q + 1 := by
  simp only [powerTwoClusterTrialTotal, triangular, Nat.mul_add]
  omega

-- This is the division-free form of the expected-hit numerator.
-- For q >= 1, the sum is N*(N-m+2)/(2*m), where N=m*q.
theorem powerTwoClusterTrialTotal_formula (m q : Nat) :
    2 * powerTwoClusterTrialTotal m (q + 1) =
      (q + 1) * (m * q + 2) := by
  have htri := triangular_double_succ q
  unfold powerTwoClusterTrialTotal
  calc
    2 * (m * triangular (q + 1) + (q + 1)) =
        m * (2 * triangular (q + 1)) + 2 * (q + 1) := by
          simp [Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]
    _ = m * (q * (q + 1)) + 2 * (q + 1) := by rw [htri]
    _ = (q + 1) * (m * q + 2) := by
          simp [Nat.mul_add, Nat.add_mul, Nat.mul_assoc,
            Nat.mul_comm, Nat.mul_left_comm]
