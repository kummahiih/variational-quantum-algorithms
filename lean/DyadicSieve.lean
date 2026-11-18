/-
  Dyadic sieve: arithmetic properties of the actual sampling pattern.

  At refinement level k, keys have the form
      (2 * index + 1) * 2^k.
  The Python generator visits levels from large k down to zero.

  This file proves that indices within one level cannot produce
  the same odd multiplier, and that two different odd multipliers
  cannot represent the same index. It also states a deterministic
  cluster coverage theorem from an explicit bounded-gap hypothesis.

  A complete proof that *all levels together* form a permutation,
  and an expected-trials comparison against a probabilistic model,
  are still future work. Avoid claiming global optimality.
-/

-- The odd multipliers used to enumerate samples at each dyadic level.
def dyadicOdd (index : Nat) : Nat := 2 * index + 1

theorem dyadicOdd_injective (i j : Nat)
    (h : dyadicOdd i = dyadicOdd j) : i = j := by
  unfold dyadicOdd at h
  omega

theorem dyadicOdd_ne_zero (i : Nat) : dyadicOdd i ≠ 0 := by
  unfold dyadicOdd
  omega

-- Sampling positions at a fixed stride; this matches the Python
-- formula (2 * index + 1) * step.
def dyadicSample (step index : Nat) : Nat :=
  dyadicOdd index * step

-- A fixed-level no-repeat theorem. The positive step is essential.
theorem dyadicSample_injective (step i j : Nat) (hstep : 0 < step)
    (h : dyadicSample step i = dyadicSample step j) : i = j := by
  unfold dyadicSample at h
  have hodd : dyadicOdd i = dyadicOdd j :=
    Nat.eq_of_mul_eq_mul_right hstep h
  exact dyadicOdd_injective i j hodd

-- Deterministic coverage implication: every sufficiently long cluster
-- is hit when the sampled keys have bounded forward gaps.
theorem cluster_hit_of_forward_cover
    (sample : Nat → Prop) (gap lo hi : Nat)
    (hcover : ∀ x : Nat, ∃ y : Nat, sample y ∧ x ≤ y ∧ y < x + gap)
    (hwidth : lo + gap ≤ hi) :
    ∃ y : Nat, sample y ∧ lo ≤ y ∧ y < hi := by
  obtain ⟨y, hs, hlo, hnear⟩ := hcover lo
  exact ⟨y, hs, hlo, Nat.lt_of_lt_of_le hnear hwidth⟩

theorem dyadic_refinement (k : Nat) :
    2 ^ (k + 1) = 2 * 2 ^ k := by
  simp [Nat.pow_succ, Nat.mul_comm]
