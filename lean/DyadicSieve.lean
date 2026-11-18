import Lean

/-
  Dyadic sieve sampling.

  sample k i = (2*i + 1) * 2^k.
  The Python implementation visits decreasing k, enumerating i from zero
  to the valid bound, then yields zero last.

  The key mathematical fact is that every positive natural number has
  at most one representation as an odd number times a power of two.
-/

def dyadicOdd (index : Nat) : Nat := 2 * index + 1

def dyadicSample (step index : Nat) : Nat :=
  dyadicOdd index * step

def sieveKey (level index : Nat) : Nat :=
  dyadicSample (2 ^ level) index

theorem dyadicOdd_injective (i j : Nat)
    (h : dyadicOdd i = dyadicOdd j) : i = j := by
  unfold dyadicOdd at h
  omega

theorem dyadicOdd_ne_zero (i : Nat) : dyadicOdd i ≠ 0 := by
  unfold dyadicOdd
  omega

theorem dyadicSample_injective (step i j : Nat) (hstep : 0 < step)
    (h : dyadicSample step i = dyadicSample step j) : i = j := by
  unfold dyadicSample at h
  have hodd : dyadicOdd i = dyadicOdd j := by
    exact Nat.eq_of_mul_eq_mul_right hstep h
  exact dyadicOdd_injective i j hodd

theorem sieveKey_zero (i : Nat) : sieveKey 0 i = 2 * i + 1 := by
  simp [sieveKey, dyadicSample, dyadicOdd]

theorem sieveKey_succ (k i : Nat) :
    sieveKey (k + 1) i = 2 * sieveKey k i := by
  simp [sieveKey, dyadicSample, Nat.pow_succ,
    Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

-- Global uniqueness, including across *different* refinement levels.
theorem sieveKey_unique (k l i j : Nat)
    (h : sieveKey k i = sieveKey l j) :
    k = l ∧ i = j := by
  induction k generalizing l i j with
  | zero =>
      cases l with
      | zero =>
          constructor
          · rfl
          · rw [sieveKey_zero, sieveKey_zero] at h
            omega
      | succ l =>
          rw [sieveKey_zero, sieveKey_succ] at h
          exfalso
          omega
  | succ k ih =>
      cases l with
      | zero =>
          rw [sieveKey_succ, sieveKey_zero] at h
          exfalso
          omega
      | succ l =>
          rw [sieveKey_succ, sieveKey_succ] at h
          have h' : sieveKey k i = sieveKey l j := by omega
          obtain ⟨hk, hi⟩ := ih l i j h'
          exact ⟨congrArg Nat.succ hk, hi⟩

-- Zero is not produced at any dyadic level; it is appended only once.
theorem sieveKey_positive (k i : Nat) : 0 < sieveKey k i := by
  unfold sieveKey dyadicSample dyadicOdd
  have hp : 0 < 2 ^ k := Nat.pow_pos (by omega)
  exact Nat.mul_pos (by omega) hp

-- A contiguous interval of width 'gap' must contain a sampled key
-- if the sampled set has forward gaps bounded by 'gap'.
theorem cluster_hit_of_forward_cover
    (sample : Nat → Prop) (gap lo hi : Nat)
    (hcover : ∀ x : Nat, ∃ y : Nat, sample y ∧ x ≤ y ∧ y < x + gap)
    (hwidth : lo + gap ≤ hi) :
    ∃ y : Nat, sample y ∧ lo ≤ y ∧ y < hi := by
  obtain ⟨y, hs, hlo, hnear⟩ := hcover lo
  exact ⟨y, hs, hlo, Nat.lt_of_lt_of_le hnear hwidth⟩

-- Unlike independent draws with replacement, distinct sieve positions
-- can never return the same positive key.
theorem sieve_no_repeated_positive_keys
    (k l i j : Nat)
    (h : sieveKey k i = sieveKey l j) :
    k = l ∧ i = j :=
  sieveKey_unique k l i j h

-- Random sampling *with replacement* allows a repeated key:
-- the following counterexample is enough to rule out a universal
-- no-repetition guarantee for that sampling model.
theorem repeated_draws_possible (key : Nat) :
    (fun _ : Nat => key) 0 = (fun _ : Nat => key) 1 := rfl

theorem dyadic_refinement (k : Nat) :
    2 ^ (k + 1) = 2 * 2 ^ k := by
  simp [Nat.pow_succ, Nat.mul_comm]
