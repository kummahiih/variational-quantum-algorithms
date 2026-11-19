import SieveHistogram
import ClusterExpectation

/-
  First-hit trials of the actual finite dyadic sieve.

  The structural lemmas in SieveHistogram prove that the first
  q-1 samples (q = 2^n) are the distinct nonzero multiples of
  m = 2^(r+1), and the next sample is m/2.

  This file defines the first-hit trial for an actual list, proves
  that a solid nonboundary cluster hits at the rank of its unique
  sampled multiple, and proves that the boundary cluster is first
  hit on trial q.

  The closed-form sum below computes the corresponding weighted
  ranks of that actual sample prefix. A final theorem equating this
  rank sum with the sum of firstHitTrial over *all* cluster starts
  remains to be formalized.
-/

-- One-based first-hit trial. An empty list has no successful hit.
def firstHitTrial : List Nat → Nat → Nat → Nat
  | [], _, _ => 0
  | key :: tail, start, width =>
      if start ≤ key ∧ key < start + width then
        1
      else
        1 + firstHitTrial tail start width

-- One-based index of a key (used only where membership is known).
def trialRank (key : Nat) : List Nat → Nat
  | [] => 0
  | head :: tail =>
      if head = key then 1 else 1 + trialRank key tail

theorem firstHitTrial_eq_rank_of_unique (key start width : Nat) :
    ∀ samples : List Nat,
      key ∈ samples →
      start ≤ key ∧ key < start + width →
      (∀ other : Nat, other ∈ samples →
        start ≤ other → other < start + width → other = key) →
      firstHitTrial samples start width = trialRank key samples := by
  intro samples
  induction samples with
  | nil =>
      intro hmem _ _
      cases hmem
  | cons head tail ih =>
      intro hmem hhit hunique
      by_cases heq : head = key
      · subst head
        simp [firstHitTrial, trialRank, hhit]
      · have hno : ¬ (start ≤ head ∧ head < start + width) := by
          intro h
          exact heq (hunique head (by simp) h.1 h.2)
        have htail : key ∈ tail := by
          rcases List.mem_cons.mp hmem with hfirst | hrest
          · exact False.elim (heq hfirst.symm)
          · exact hrest
        have huniqueTail :
            ∀ other : Nat, other ∈ tail →
              start ≤ other → other < start + width →
              other = key := by
          intro other hm hlo hhi
          exact hunique other (by simp [hm]) hlo hhi
        have hi := ih htail hhit huniqueTail
        simp [firstHitTrial, trialRank, heq, hno, hi]

-- Every one of the m cluster starts within an aligned block hits
-- its unique positive multiple of m. The rank uses the *real*
-- coarse-to-fine list.
theorem firstHitTrial_block (n r j i : Nat)
    (hj : j + 1 < 2 ^ n) (hi : i < 2 ^ (r + 1)) :
    let m := 2 ^ (r + 1)
    let samples := (positiveSieve (n + r + 1)).take (2 ^ n - 1)
    let start := j * m + i + 1
    firstHitTrial samples start m =
      trialRank (m * (j + 1)) samples := by
  dsimp
  let m := 2 ^ (r + 1)
  let samples := (positiveSieve (n + r + 1)).take (2 ^ n - 1)
  let start := j * m + i + 1
  have hblock : uniqueClusterHit samples start m := by
    simpa [samples, start, m, Nat.add_assoc] using
      positiveSieve_cluster_block n (r + 1) j hj i hi
  obtain ⟨found, ⟨hfound, hfoundLo, hfoundHi⟩, hunique⟩ := hblock
  have hmem : m * (j + 1) ∈ samples := by
    exact positiveSieve_prefix_is_multiples n (r + 1) (j + 1)
      (by omega) hj
  have hstep : (j + 1) * m = j * m + m := by
    simp [Nat.add_mul]
  have hbounds : start ≤ m * (j + 1) ∧
      m * (j + 1) < start + m := by
    have hprod : m * (j + 1) = j * m + m := by
      rw [Nat.mul_comm]
      exact hstep
    have him : i < m := hi
    dsimp [start]
    rw [hprod]
    constructor <;> omega
  have hfoundEq : m * (j + 1) = found :=
    hunique (m * (j + 1)) ⟨hmem, hbounds.1, hbounds.2⟩
  apply firstHitTrial_eq_rank_of_unique
  · exact hmem
  · exact hbounds
  · intro other hm hlo hhi
    calc
      other = found := hunique other ⟨hm, hlo, hhi⟩
      _ = m * (j + 1) := hfoundEq.symm

theorem firstHitTrial_append_no_hit (start width : Nat) :
    ∀ before after : List Nat,
      (∀ x : Nat, x ∈ before →
         ¬ (start ≤ x ∧ x < start + width)) →
      firstHitTrial (before ++ after) start width =
        before.length + firstHitTrial after start width := by
  intro before
  induction before with
  | nil =>
      intro after _
      simp [firstHitTrial]
  | cons head tail ih =>
      intro after hno
      have hhead : ¬ (start ≤ head ∧ head < start + width) :=
        hno head (by simp)
      have htail : ∀ x, x ∈ tail →
          ¬ (start ≤ x ∧ x < start + width) := by
        intro x hx
        exact hno x (by simp [hx])
      have hr := ih after htail
      simp [firstHitTrial, hhead, hr, Nat.add_assoc, Nat.add_comm, Nat.add_left_comm]

-- The zero-start cluster [0,m) is not hit by any of the q-1
-- nonzero multiples of m. Trial q samples m/2 and hits it.
theorem firstHitTrial_boundary (n r : Nat) :
    firstHitTrial
      ((positiveSieve (n + r + 1)).take (2 ^ n))
      0 (2 ^ (r + 1)) = 2 ^ n := by
  rw [positiveSieve_first_q]
  let m := 2 ^ (r + 1)
  let before := (positiveSieve n).map (fun x => m * x)
  have hno : ∀ x : Nat, x ∈ before →
      ¬ (0 ≤ x ∧ x < m) := by
    intro x hx h
    obtain ⟨k, hk, heq⟩ := List.mem_map.mp hx
    have hkpos := (positiveSieve_bounds n k hk).1
    have hle : m * 1 ≤ m * k :=
      Nat.mul_le_mul_left m (by omega)
    omega
  have htail : firstHitTrial [2 ^ r] 0 m = 1 := by
    have hsmall : 2 ^ r < m := by
      have hp : 0 < 2 ^ r := Nat.pow_pos (by omega)
      dsimp [m]
      rw [Nat.pow_succ]
      omega
    simp [firstHitTrial, hsmall]
  have hlength := positiveSieve_length n
  have hno' : ∀ x : Nat, x ∈ before →
      ¬ (0 ≤ x ∧ x < 0 + m) := by
    simpa only [Nat.zero_add] using hno
  have happend := firstHitTrial_append_no_hit 0 m before [2 ^ r] hno'
  change firstHitTrial (before ++ [2 ^ r]) 0 m = 2 ^ n
  rw [happend, htail]
  simpa [before] using hlength

-- The sum of 1+f(x) over a list is its length plus the sum of f(x).
theorem sum_one_plus_map (f : Nat → Nat) :
    ∀ xs : List Nat,
      (xs.map (fun x => 1 + f x)).sum =
        xs.length + (xs.map f).sum := by
  intro xs
  induction xs with
  | nil => simp
  | cons x xs ih =>
      simp only [List.map_cons, List.sum_cons, List.length_cons]
      omega

theorem sum_ranks_tail (key : Nat) (xs : List Nat)
    (hnot : key ∉ xs) :
    (xs.map (fun x => trialRank x (key :: xs))).sum =
      xs.length + (xs.map (fun x => trialRank x xs)).sum := by
  have hmap :
      xs.map (fun x => trialRank x (key :: xs)) =
        xs.map (fun x => 1 + trialRank x xs) := by
    apply List.map_congr_left
    intro x hx
    have hne : key ≠ x := by
      intro heq
      apply hnot
      simpa [heq] using hx
    simp [trialRank, hne]
  rw [hmap]
  exact sum_one_plus_map (fun x => trialRank x xs) xs

-- Ranks 1,...,length appear once each in every nodup list.
-- Their sum is the triangular number of the list's length.
theorem sum_sample_ranks :
    ∀ xs : List Nat, xs.Nodup →
      (xs.map (fun x => trialRank x xs)).sum =
        triangular (xs.length + 1) := by
  intro xs
  induction xs with
  | nil =>
      intro _
      simp [triangular]
  | cons key xs ih =>
      intro hn
      have hnot := (List.nodup_cons.mp hn).1
      have hnTail := (List.nodup_cons.mp hn).2
      have hsum := sum_ranks_tail key xs hnot
      have hrec := ih hnTail
      calc
        ((key :: xs).map
            (fun x => trialRank x (key :: xs))).sum =
            1 + (xs.map (fun x => trialRank x (key :: xs))).sum := by
              simp [trialRank]
        _ = 1 + xs.length + (xs.map (fun x => trialRank x xs)).sum := by
              rw [hsum]
              omega
        _ = triangular ((key :: xs).length + 1) := by
              simp only [List.length_cons]
              rw [show xs.length + 1 + 1 =
                (xs.length + 1) + 1 by omega, triangular, ← hrec]
              omega

-- The weighted rank total obtained from the actual dyadic prefix.
-- Each of its q-1 unique multiples corresponds to m cluster starts,
-- and the zero-start boundary cluster is first hit on trial q.
def sieveClusterTrialTotal (n r : Nat) : Nat :=
  let small := positiveSieve n
  2 ^ (r + 1) * (small.map (fun key => trialRank key small)).sum + 2 ^ n

-- Arithmetic closed form of the rank total for the real finite sieve.
-- The remaining formal step is equality with the sum over all starts.
theorem sieveClusterTrialTotal_formula (n r : Nat) :
    2 * sieveClusterTrialTotal n r =
      (2 ^ n) * (2 ^ (r + 1) * (2 ^ n - 1) + 2) := by
  have hlen := positiveSieve_length n
  have hsum :
      ((positiveSieve n).map
        (fun x => trialRank x (positiveSieve n))).sum =
          triangular (2 ^ n) := by
    rw [sum_sample_ranks (positiveSieve n) (positiveSieve_nodup n)]
    rw [hlen]
  have hq : (2 ^ n - 1) + 1 = 2 ^ n := by
    have hp : 0 < 2 ^ n := Nat.pow_pos (by omega)
    omega
  have htri := powerTwoClusterTrialTotal_formula (2 ^ (r + 1)) (2 ^ n - 1)
  unfold sieveClusterTrialTotal
  dsimp
  rw [hsum, ← hq]
  exact htri

#eval firstHitTrial (positiveSieve 4 ++ [0]) 1 4
#eval firstHitTrial (positiveSieve 4 ++ [0]) 0 4
