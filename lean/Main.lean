-- Initial Lean 4 entry point. Add proofs as the study develops.
theorem identity_example (p : Prop) : p → p := by
  intro hp
  exact hp
