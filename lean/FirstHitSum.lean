import FirstHitExpectation

/-
  Sum first-hit trials over every legal solid-cluster starting position.

  The following development does not assume a first-hit histogram.
  It uses the concrete firstHitTrial function on the initial q samples
  of positiveSieve, with q = 2^n, m = 2^(r+1).

  The last theorem proves the unnormalized expected-time identity.
  Dividing its two sides by the number of possible cluster starts
  gives the mean hit time under a uniform cluster-start distribution.

  The m = 1 case (where zero, rather than m/2, is the last key)
  is treated separately in future work.
-/

def actualFirstHit (n r start : Nat) : Nat :=
  firstHitTrial
    ((positiveSieve (n + r + 1)).take (2 ^ n))
    start (2 ^ (r + 1))

-- Summation of a contiguous block of positions, with no dependencies
-- on any third-party big-operator library.
def intervalTrialSum (start : Nat) : Nat → (Nat → Nat) → Nat
  | 0, _ => 0
  | count + 1, f =>
      intervalTrialSum start count f + f (start + count)

theorem clusterTrialSum_extend (start count : Nat) (f : Nat → Nat) :
    clusterTrialSum (start + count) f =
      clusterTrialSum start f + intervalTrialSum start count f := by
  induction count with
  | zero =>
      simp [intervalTrialSum]
  | succ count ih =>
      rw [show start + (count + 1) = (start + count) + 1 by omega]
      rw [clusterTrialSum, ih, intervalTrialSum]
      omega

theorem intervalTrialSum_constant (start count value : Nat)
    (f : Nat → Nat)
    (h : ∀ i < count, f (start + i) = value) :
    intervalTrialSum start count f = count * value := by
  induction count with
  | zero =>
      simp [intervalTrialSum]
  | succ count ih =>
      have hp : ∀ i < count, f (start + i) = value := by
        intro i hi
        exact h i (by omega)
      have hv : f (start + count) = value := h count (by omega)
      rw [intervalTrialSum, ih hp, hv, Nat.succ_mul]

-- Group the sum over starts 0,...,q*m into the singleton start 0
-- and q successive blocks, each containing m positive starts.
theorem clusterTrialSum_by_blocks (q m : Nat) (f : Nat → Nat) :
    clusterTrialSum (q * m + 1) f =
      f 0 +
        clusterTrialSum q
          (fun j => intervalTrialSum (j * m + 1) m f) := by
  induction q with
  | zero =>
      simp [clusterTrialSum]
  | succ q ih =>
      have hextend := clusterTrialSum_extend (q * m + 1) m f
      have hidx : (q + 1) * m + 1 = (q * m + 1) + m := by
        rw [Nat.add_mul]
        omega
      rw [hidx, hextend, ih, clusterTrialSum]
      omega

theorem clusterTrialSum_congr (count : Nat) (f g : Nat → Nat)
    (h : ∀ i < count, f i = g i) :
    clusterTrialSum count f = clusterTrialSum count g := by
  induction count with
  | zero =>
      simp [clusterTrialSum]
  | succ count ih =>
      have hp : ∀ i < count, f i = g i := by
        intro i hi
        exact h i (by omega)
      have hv : f count = g count := h count (by omega)
      rw [clusterTrialSum, clusterTrialSum, ih hp, hv]

theorem clusterTrialSum_mul (count factor : Nat) (f : Nat → Nat) :
    clusterTrialSum count (fun i => factor * f i) =
      factor * clusterTrialSum count f := by
  induction count with
  | zero =>
      simp [clusterTrialSum]
  | succ count ih =>
      rw [clusterTrialSum, clusterTrialSum, ih, Nat.mul_add]

-- Appending later samples cannot change a first hit that is already
-- present in the earlier list.
theorem firstHitTrial_append_hit (start width : Nat) :
    ∀ before after : List Nat,
      (∃ key : Nat,
        key ∈ before ∧ start ≤ key ∧ key < start + width) →
      firstHitTrial (before ++ after) start width =
        firstHitTrial before start width := by
  intro before
  induction before with
  | nil =>
      intro after ⟨key, hmem, _, _⟩
      cases hmem
  | cons head tail ih =>
      intro after hh
      by_cases hhead : start ≤ head ∧ head < start + width
      · simp [firstHitTrial, hhead]
      · obtain ⟨key, hmem, hlo, hhi⟩ := hh
        have htail : key ∈ tail := by
          rcases List.mem_cons.mp hmem with hfirst | hrest
          · subst key
            exact False.elim (hhead ⟨hlo, hhi⟩)
          · exact hrest
        have hr := ih after ⟨key, htail, hlo, hhi⟩
        simp [firstHitTrial, hhead, hr]

-- Scaling every sampled key by a positive factor preserves its rank.
theorem trialRank_mul_map (factor key : Nat) (hfactor : 0 < factor) :
    ∀ samples : List Nat,
      trialRank (factor * key)
        (samples.map (fun x => factor * x)) =
      trialRank key samples := by
  intro samples
  induction samples with
  | nil => rfl
  | cons head tail ih =>
      by_cases h : head = key
      · subst head
        simp [trialRank]
      · have hmul : factor * head ≠ factor * key := by
          intro heq
          exact h (Nat.eq_of_mul_eq_mul_left hfactor heq)
        simp [trialRank, h, hmul, ih]

-- A nonboundary cluster is first hit at the rank of the one
-- positive multiple of m in its interval, in the actual q-key samplePrefix.
theorem actualFirstHit_block (n r j i : Nat)
    (hj : j + 1 < 2 ^ n) (hi : i < 2 ^ (r + 1)) :
    actualFirstHit n r (j * 2 ^ (r + 1) + i + 1) =
      trialRank (j + 1) (positiveSieve n) := by
  let m := 2 ^ (r + 1)
  let start := j * m + i + 1
  let samplePrefix := (positiveSieve n).map (fun x => m * x)
  have hprefix :
      (positiveSieve (n + r + 1)).take (2 ^ n - 1) = samplePrefix := by
    simpa [samplePrefix, m, Nat.add_assoc] using
      positiveSieve_prefix n (r + 1)
  have hfull :
      (positiveSieve (n + r + 1)).take (2 ^ n) =
        samplePrefix ++ [2 ^ r] := by
    simpa [samplePrefix, m, Nat.add_assoc] using
      positiveSieve_first_q n r
  have hmem : m * (j + 1) ∈ samplePrefix := by
    apply List.mem_map.mpr
    exact ⟨j + 1, positiveSieve_complete n (j + 1)
      (by omega) hj, rfl⟩
  have hprod : m * (j + 1) = j * m + m := by
    calc
      m * (j + 1) = (j + 1) * m := Nat.mul_comm _ _
      _ = j * m + m := by simp [Nat.add_mul]
  have hbounds :
      start ≤ m * (j + 1) ∧
      m * (j + 1) < start + m := by
    have him : i < m := hi
    dsimp [start]
    rw [hprod]
    constructor <;> omega
  have hstable := firstHitTrial_append_hit start m samplePrefix [2 ^ r]
    ⟨m * (j + 1), hmem, hbounds.1, hbounds.2⟩
  have hblock := firstHitTrial_block n r j i hj hi
  dsimp at hblock
  rw [hprefix] at hblock
  have hrank := trialRank_mul_map m (j + 1)
    (Nat.pow_pos (by omega)) (positiveSieve n)
  change firstHitTrial
    ((positiveSieve (n + r + 1)).take (2 ^ n))
    start m = trialRank (j + 1) (positiveSieve n)
  rw [hfull, hstable]
  exact hblock.trans hrank

theorem actualFirstHit_zero (n r : Nat) :
    actualFirstHit n r 0 = 2 ^ n :=
  firstHitTrial_boundary n r

-- The entire block of m starts has constant first-hit rank.
theorem actualFirstHit_interval (n r j : Nat)
    (hj : j + 1 < 2 ^ n) :
    intervalTrialSum (j * 2 ^ (r + 1) + 1)
      (2 ^ (r + 1)) (actualFirstHit n r) =
    2 ^ (r + 1) * trialRank (j + 1) (positiveSieve n) := by
  apply intervalTrialSum_constant
  intro i hi
  have h := actualFirstHit_block n r j i hj hi
  simpa [Nat.add_assoc, Nat.add_comm, Nat.add_left_comm] using h

-- Sum over the concrete starts 0,...,(q-1)*m.
theorem actualFirstHit_sum_by_blocks (n r : Nat) :
    clusterTrialSum ((2 ^ n - 1) * 2 ^ (r + 1) + 1)
      (actualFirstHit n r) =
    2 ^ n +
      2 ^ (r + 1) *
        clusterTrialSum (2 ^ n - 1)
          (fun j => trialRank (j + 1) (positiveSieve n)) := by
  let q := 2 ^ n - 1
  let m := 2 ^ (r + 1)
  have hp := clusterTrialSum_by_blocks q m (actualFirstHit n r)
  have hblocks : ∀ j < q,
      intervalTrialSum (j * m + 1) m (actualFirstHit n r) =
        m * trialRank (j + 1) (positiveSieve n) := by
    intro j hj
    exact actualFirstHit_interval n r j (by
      dsimp [q] at hj
      omega)
  have heq := clusterTrialSum_congr q
    (fun j => intervalTrialSum (j * m + 1) m (actualFirstHit n r))
    (fun j => m * trialRank (j + 1) (positiveSieve n)) hblocks
  rw [heq, clusterTrialSum_mul] at hp
  rw [actualFirstHit_zero] at hp
  exact hp

-- The recursive clusterTrialSum is the sum of a mapped range.
theorem clusterTrialSum_range (count : Nat) (f : Nat → Nat) :
    clusterTrialSum count f =
      ((List.range count).map f).sum := by
  induction count with
  | zero =>
      simp [clusterTrialSum]
  | succ count ih =>
      rw [clusterTrialSum, ih, List.range_succ]
      simp [List.map_append, List.sum_append]

-- The numerical order of positive keys is a permutation of the
-- actual coarse-to-fine positiveSieve list.
theorem positiveSieve_range_perm (n : Nat) :
    ((List.range (2 ^ n - 1)).map (fun j => j + 1)).Perm
      (positiveSieve n) := by
  have hd : ((List.range (2 ^ n - 1)).map
      (fun j => j + 1)).Nodup := by
    exact List.Pairwise.map
      (fun j : Nat => j + 1)
      (fun a b hab heq => hab (by omega))
      (List.nodup_range)
  apply (List.perm_ext_iff_of_nodup hd (positiveSieve_nodup n)).2
  intro x
  constructor
  · intro h
    obtain ⟨j, hj, heq⟩ := List.mem_map.mp h
    have hj' := List.mem_range.mp hj
    apply positiveSieve_complete n x
    · omega
    · omega
  · intro h
    have hb := positiveSieve_bounds n x h
    apply List.mem_map.mpr
    refine ⟨x - 1, List.mem_range.mpr (by omega), ?_⟩
    omega

-- Ranks over all 1,...,q-1 equal ranks over the actual sieve list.
theorem positiveSieve_range_rank_sum (n : Nat) :
    clusterTrialSum (2 ^ n - 1)
      (fun j => trialRank (j + 1) (positiveSieve n)) =
    ((positiveSieve n).map
      (fun key => trialRank key (positiveSieve n))).sum := by
  rw [clusterTrialSum_range]
  have hp := (positiveSieve_range_perm n).map
    (fun key => trialRank key (positiveSieve n))
  have hs := hp.sum_nat
  simpa [List.map_map] using hs

-- The previously proved weighted-rank total is *exactly* the sum
-- of firstHitTrial over all possible cluster starts (m >= 2).
theorem actualFirstHit_total (n r : Nat) :
    clusterTrialSum ((2 ^ n - 1) * 2 ^ (r + 1) + 1)
      (actualFirstHit n r) =
    sieveClusterTrialTotal n r := by
  rw [actualFirstHit_sum_by_blocks, positiveSieve_range_rank_sum]
  simp [sieveClusterTrialTotal, Nat.add_comm]

-- End-to-end unnormalized expectation theorem, established directly
-- from the finite dyadic sample order with no histogram hypothesis.
theorem actualFirstHit_total_formula (n r : Nat) :
    2 * clusterTrialSum
      ((2 ^ n - 1) * 2 ^ (r + 1) + 1)
      (actualFirstHit n r) =
    (2 ^ n) * (2 ^ (r + 1) * (2 ^ n - 1) + 2) := by
  rw [actualFirstHit_total]
  exact sieveClusterTrialTotal_formula n r

#eval clusterTrialSum 13 (actualFirstHit 2 1)
-- N = 16, m = 4, q = 4; expected numerator = 28.
