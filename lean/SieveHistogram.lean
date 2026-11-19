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

  The eventual first-hit histogram still needs a theorem about the
  first sample strictly below m (and a formal first-hit-time function).
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
        Nat.pow_succ, Nat.mul_assoc, Nat.mul_comm, Nat.mul_left_comm]

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
  by_contra hne
  have hcases : k < j ∨ j < k := by omega
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
          omega
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

#eval positiveSieve 4
-- [8, 4, 12, 2, 6, 10, 14, 1, 3, 5, 7, 9, 11, 13, 15]
#eval (positiveSieve 4).take 3
-- [8, 4, 12], the first q-1 samples for m = 4.
