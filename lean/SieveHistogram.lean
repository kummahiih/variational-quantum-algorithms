import Lean

/-
  Actual finite dyadic midpoint order.

  positiveSieve n lists the positive keys of the n-bit sieve, in
  exactly the same coarse-to-fine order as Python's keys(n).
  The next width first doubles every earlier key, then visits all
  odd keys in increasing order. Zero is appended at the end in Python.

  The prefix theorem below is the key non-axiomatic step towards the
  solid-cluster histogram: for N = 2^(n+r) and m = 2^r, the first
  2^n - 1 positive samples are precisely the positive multiples of m.

  The proofs below establish the complete positive-multiple prefix,
  the very next midpoint, and uniqueness of the hit for every
  nonboundary aligned cluster-start block. A single theorem phrased in
  terms of a numeric first-hit-time function and its trial histogram
  remains to be assembled.
-/

def positiveSieve : Nat → List Nat
  | 0 => []
  | n + 1 =>
      (positiveSieve n).map (fun x => 2 * x) ++
      (List.range (2 ^ n)).map (fun i => 2 * i + 1)

theorem positiveSieve_length (n : Nat) :
    (positiveSieve n).length + 1 = 2 ^ n := by
  induction n with
  | zero =>
      simp [positiveSieve]
  | succ n ih =>
      simp only [positiveSieve, List.length_append,
        List.length_map, List.length_range]
      rw [Nat.pow_succ]
      omega

theorem positiveSieve_bounds (n x : Nat)
    (h : x ∈ positiveSieve n) :
    0 < x ∧ x < 2 ^ n := by
  induction n generalizing x with
  | zero =>
      simp [positiveSieve] at h
  | succ n ih =>
      have hp : 2 ^ (n + 1) = 2 * 2 ^ n := by
        simp [Nat.pow_succ, Nat.mul_comm]
      simp only [positiveSieve, List.mem_append, List.mem_map] at h
      rcases h with ⟨y, hy, heq⟩ | ⟨i, hi, heq⟩
      · have hb := ih y hy
        rw [hp]
        omega
      · have hb := List.mem_range.mp hi
        rw [hp]
        omega

theorem positiveSieve_complete (n x : Nat)
    (hpos : 0 < x) (hlt : x < 2 ^ n) :
    x ∈ positiveSieve n := by
  induction n generalizing x with
  | zero =>
      omega
  | succ n ih =>
      have hp : 2 ^ (n + 1) = 2 * 2 ^ n := by
        simp [Nat.pow_succ, Nat.mul_comm]
      rw [hp] at hlt
      simp only [positiveSieve, List.mem_append, List.mem_map]
      by_cases heven : x % 2 = 0
      · left
        refine ⟨x / 2, ?_, ?_⟩
        · apply ih
          · omega
          · omega
        · omega
      · right
        refine ⟨x / 2, List.mem_range.mpr (by omega), ?_⟩
        omega

theorem positiveSieve_nodup (n : Nat) :
    (positiveSieve n).Nodup := by
  induction n with
  | zero =>
      simp [positiveSieve]
  | succ n ih =>
      rw [positiveSieve, List.nodup_append]
      refine ⟨?_, ?_, ?_⟩
      · exact List.Pairwise.map
          (fun x : Nat => 2 * x)
          (fun a b hab heq => hab (by omega))
          ih
      · exact List.Pairwise.map
          (fun i : Nat => 2 * i + 1)
          (fun a b hab heq => hab (by omega))
          (List.nodup_range)
      · intro a ha b hb heq
        obtain ⟨x, hx, ha'⟩ := List.mem_map.mp ha
        obtain ⟨i, hi, hb'⟩ := List.mem_map.mp hb
        omega

-- Prefix lemma: the beginning of the larger sieve is the smaller
-- sieve scaled by a power of two; no ordering assumptions are needed.
theorem positiveSieve_scaled_prefix (n r : Nat) :
    ∃ tail : List Nat,
      positiveSieve (n + r) =
        (positiveSieve n).map (fun x => 2 ^ r * x) ++ tail := by
  induction r with
  | zero =>
      refine ⟨[], ?_⟩
      simp
  | succ r ih =>
      obtain ⟨tail, htail⟩ := ih
      refine ⟨tail.map (fun x => 2 * x) ++
        (List.range (2 ^ (n + r))).map (fun i => 2 * i + 1), ?_⟩
      rw [Nat.add_succ, positiveSieve, htail]
      simp [List.map_append, List.map_map, List.append_assoc,
        Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm]

theorem positiveSieve_prefix (n r : Nat) :
    (positiveSieve (n + r)).take (2 ^ n - 1) =
      (positiveSieve n).map (fun x => 2 ^ r * x) := by
  obtain ⟨tail, htail⟩ := positiveSieve_scaled_prefix n r
  rw [htail]
  have hlen :
      ((positiveSieve n).map (fun x => 2 ^ r * x)).length =
        2 ^ n - 1 := by
    have h := positiveSieve_length n
    simp only [List.length_map]
    omega
  rw [← hlen]
  exact List.take_append_length


-- The odd-key group always starts with key 1.
theorem oddGroup_head (n : Nat) :
    ∃ tail : List Nat,
      (List.range (2 ^ n)).map (fun i => 2 * i + 1) = 1 :: tail := by
  have hp : 0 < 2 ^ n := Nat.pow_pos (by omega)
  have hn : 2 ^ n = (2 ^ n - 1) + 1 := by omega
  rw [hn, List.range_succ_eq_map]
  exact ⟨_, rfl⟩

-- After the first 2^n - 1 multiples of m = 2^(r+1), the very
-- next sample is m/2 = 2^r (the new refinement level's first key).
theorem positiveSieve_scaled_next (n r : Nat) :
    ∃ tail : List Nat,
      positiveSieve (n + r + 1) =
        (positiveSieve n).map (fun x => 2 ^ (r + 1) * x) ++
        (2 ^ r :: tail) := by
  induction r with
  | zero =>
      obtain ⟨tail, hodd⟩ := oddGroup_head n
      refine ⟨tail, ?_⟩
      simp [positiveSieve, hodd, Nat.pow_succ]
  | succ r ih =>
      obtain ⟨tail, htail⟩ := ih
      refine ⟨tail.map (fun x => 2 * x) ++
        (List.range (2 ^ (n + r + 1))).map (fun i => 2 * i + 1), ?_⟩
      have hindex : n + (r + 1) + 1 = (n + r + 1) + 1 := by omega
      rw [hindex, positiveSieve, htail]
      simp [List.map_append, List.map_map, List.append_assoc,
        Nat.pow_succ, Nat.mul_comm, Nat.mul_left_comm]

-- This also identifies the boundary trial without a probabilistic
-- or first-hit assumption.
theorem positiveSieve_first_q (n r : Nat) :
    (positiveSieve (n + r + 1)).take (2 ^ n) =
      (positiveSieve n).map (fun x => 2 ^ (r + 1) * x) ++
      [2 ^ r] := by
  obtain ⟨tail, htail⟩ := positiveSieve_scaled_next n r
  rw [htail]
  have hlen :
      ((positiveSieve n).map (fun x => 2 ^ (r + 1) * x)).length + 1 =
        2 ^ n := by
    simpa only [List.length_map] using positiveSieve_length n
  rw [← hlen, List.take_length_add_append]
  rfl

-- Every key from the earlier prefix is at least m, so none can
-- hit the cluster [0,m). Its first hit is the next key m/2.
theorem positiveSieve_prefix_ge (n r x : Nat)
    (hx : x ∈ (positiveSieve (n + r)).take (2 ^ n - 1)) :
    2 ^ r ≤ x := by
  rw [positiveSieve_prefix] at hx
  obtain ⟨j, hj, hkey⟩ := List.mem_map.mp hx
  have hpos := (positiveSieve_bounds n j hj).1
  have hle : (2 ^ r) * 1 ≤ (2 ^ r) * j :=
    Nat.mul_le_mul_left (2 ^ r) (by omega)
  omega

theorem positiveSieve_boundary_new_hit (n r : Nat) :
    2 ^ r < 2 ^ (r + 1) ∧
    (∀ x ∈ (positiveSieve (n + r + 1)).take (2 ^ n - 1),
      2 ^ (r + 1) ≤ x) := by
  constructor
  · have hp : 0 < 2 ^ r := Nat.pow_pos (by omega)
    rw [Nat.pow_succ]
    omega
  · intro x hx
    have hx' :
        x ∈ (positiveSieve (n + (r + 1))).take (2 ^ n - 1) := by
      simpa [Nat.add_assoc] using hx
    exact positiveSieve_prefix_ge n (r + 1) x hx'

-- Each positive multiple of m contributes precisely the m cluster
-- starts immediately preceding that multiple. This is the arithmetic
-- reason the first-hit histogram is flat.
theorem aligned_cluster_contains (j m a : Nat)
    (hlo : j * m < a) (hhi : a ≤ (j + 1) * m) :
    a ≤ (j + 1) * m ∧ (j + 1) * m < a + m := by
  constructor
  · exact hhi
  · have hstep : (j + 1) * m = j * m + m := by
      simp [Nat.add_mul]
    omega

-- A length-m interval from such a block cannot contain a different
-- positive multiple of m. No probabilistic or coverage assumption.
theorem aligned_cluster_unique (j k m a : Nat)
    (hlo : j * m < a) (hhi : a ≤ (j + 1) * m)
    (hhitLo : a ≤ (k + 1) * m)
    (hhitHi : (k + 1) * m < a + m) :
    j = k := by
  by_cases heq : j = k
  · exact heq
  · have hcases : k < j ∨ j < k := by omega
    rcases hcases with hk | hk
    · have hle : k + 1 ≤ j := by omega
      have hmle := Nat.mul_le_mul_right m hle
      omega
    · have hle : j + 2 ≤ k + 1 := by omega
      have hmle := Nat.mul_le_mul_right m hle
      have hstep : (j + 2) * m = (j + 1) * m + m := by
        calc
          (j + 2) * m = ((j + 1) + 1) * m := by
            congr 1
          _ = (j + 1) * m + m := by
            simp [Nat.add_mul]
      omega


-- The first 2^n-1 samples consist of the q-1 nonzero multiples of
-- m=2^r, with no repeats. They are also all strictly below N.
theorem positiveSieve_prefix_is_multiples (n r : Nat) :
    ∀ j, 0 < j → j < 2 ^ n →
      2 ^ r * j ∈
        (positiveSieve (n + r)).take (2 ^ n - 1) := by
  intro j hpos hlt
  rw [positiveSieve_prefix]
  apply List.mem_map.mpr
  exact ⟨j, positiveSieve_complete n j hpos hlt, rfl⟩

-- The order has no repeated keys even when truncated to its prefix.
theorem positiveSieve_prefix_nodup (n r : Nat) :
    ((positiveSieve (n + r)).take (2 ^ n - 1)).Nodup := by
  exact (positiveSieve_nodup (n + r)).take

-- Explicit uniqueness predicate: finite list of sampled keys contains
-- exactly one hit in the specified half-open interval.
def uniqueClusterHit (samples : List Nat) (start width : Nat) : Prop :=
  ∃ key : Nat,
    (key ∈ samples ∧ start ≤ key ∧ key < start + width) ∧
    ∀ other : Nat,
      (other ∈ samples ∧ start ≤ other ∧ other < start + width) →
      other = key

-- Every nonboundary solid cluster has exactly one successful key
-- among the first q-1 samples, namely the next positive multiple of m.
-- This statement refers to the *actual* finite sieve list.
theorem positiveSieve_cluster_unique_hit (n r j a : Nat)
    (hj : j + 1 < 2 ^ n)
    (hlo : j * 2 ^ r < a)
    (hhi : a ≤ (j + 1) * 2 ^ r) :
    uniqueClusterHit
      ((positiveSieve (n + r)).take (2 ^ n - 1)) a (2 ^ r) := by
  let m := 2 ^ r
  have hpos : 0 < j + 1 := by omega
  have hmem : m * (j + 1) ∈
      (positiveSieve (n + r)).take (2 ^ n - 1) :=
    positiveSieve_prefix_is_multiples n r (j + 1) hpos hj
  have hh := aligned_cluster_contains j m a hlo hhi
  have hgoal : m * (j + 1) = (j + 1) * m := Nat.mul_comm _ _
  unfold uniqueClusterHit
  refine ⟨m * (j + 1), ⟨⟨hmem, ?_, ?_⟩, ?_⟩⟩
  · simpa [hgoal] using hh.1
  · simpa [hgoal] using hh.2
  · intro key hkey
    obtain ⟨hkeymem, hstart, hend⟩ := hkey
    rw [positiveSieve_prefix] at hkeymem
    obtain ⟨k, hk, heq⟩ := List.mem_map.mp hkeymem
    have hkpos := (positiveSieve_bounds n k hk).1
    have hkstep : k - 1 + 1 = k := by omega
    have hkeyform : (k - 1 + 1) * m = key := by
      rw [hkstep, Nat.mul_comm]
      exact heq
    have hblock : j = k - 1 := by
      apply aligned_cluster_unique j (k - 1) m a hlo hhi
      · rw [hkeyform]
        exact hstart
      · rw [hkeyform]
        exact hend
    have hsame : k = j + 1 := by omega
    rw [hsame] at heq
    simpa [m] using heq.symm

-- A block contains exactly m consecutive starts and every one of
-- them has the corresponding unique positive-multiple hit.
theorem positiveSieve_cluster_block (n r j : Nat)
    (hj : j + 1 < 2 ^ n) :
    ∀ i < 2 ^ r,
      uniqueClusterHit
        ((positiveSieve (n + r)).take (2 ^ n - 1))
        (j * 2 ^ r + i + 1) (2 ^ r) := by
  intro i hi
  have hstep : (j + 1) * 2 ^ r = j * 2 ^ r + 2 ^ r := by
    simp [Nat.add_mul]
  apply positiveSieve_cluster_unique_hit n r j (j * 2 ^ r + i + 1) hj
  · omega
  · omega

theorem positiveSieve_block_start_count (j m : Nat) :
    ((List.range m).map (fun i => j * m + i + 1)).length = m := by
  simp



-- Combined certificate for m = 2^(r+1) and q = 2^n:
--   * q-1 distinct positive multiples of m precede m/2;
--   * each of the m starts in every nonboundary block has a
--     unique successful key in that q-1-key prefix.
-- Consequently the successful trial for each block is the rank
-- of its multiple, and each of the q-1 ranks occurs m times.
theorem positiveSieve_histogram_certificate (n r : Nat) :
    (positiveSieve (n + r + 1)).take (2 ^ n) =
      (positiveSieve n).map (fun x => 2 ^ (r + 1) * x) ++ [2 ^ r]
    ∧
    (∀ j, j + 1 < 2 ^ n →
      ∀ i < 2 ^ (r + 1),
        uniqueClusterHit
          ((positiveSieve (n + r + 1)).take (2 ^ n - 1))
          (j * 2 ^ (r + 1) + i + 1) (2 ^ (r + 1)))
    ∧
    ((positiveSieve (n + r + 1)).take (2 ^ n - 1)).Nodup := by
  refine ⟨positiveSieve_first_q n r, ?_, ?_⟩
  · intro j hj i hi
    have h := positiveSieve_cluster_block n (r + 1) j hj i hi
    simpa [Nat.add_assoc] using h
  · simpa [Nat.add_assoc] using (positiveSieve_prefix_nodup n (r + 1))

#eval positiveSieve 4
-- [8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15]
#eval (positiveSieve 4).take 3
-- [8, 4, 12], the first q-1 samples for m = 4.
