/-
  Cluster coverage lemma for a coarse-to-fine sieve.

  This proves a sufficient condition for detecting any contiguous cluster:
  if the sampled keys have forward gaps smaller than 'gap', then every
  interval of length at least 'gap' contains a sampled key.

  It does NOT prove that the dyadic ordering minimizes expected trials:
  such an optimality claim requires a precise distribution of clusters
  and a specified class of competing algorithms.
-/

theorem cluster_hit_of_forward_cover
    (sample : Nat → Prop) (gap lo hi : Nat)
    (hcover : ∀ x : Nat, ∃ y : Nat, sample y ∧ x ≤ y ∧ y < x + gap)
    (hwidth : lo + gap ≤ hi) :
    ∃ y : Nat, sample y ∧ lo ≤ y ∧ y < hi := by
  obtain ⟨y, hs, hlo, hnear⟩ := hcover lo
  exact ⟨y, hs, hlo, Nat.lt_of_lt_of_le hnear hwidth⟩

-- Each successive refinement halves the spacing.
theorem dyadic_refinement (k : Nat) :
    2 ^ (k + 1) = 2 * 2 ^ k := by
  simp [pow_succ, Nat.mul_comm]
