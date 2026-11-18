# Agent notes

For related SDK documentation, VQA examples, and neighboring repositories, see [docs/neighbors.md](docs/neighbors.md).

Keep `src/` flat and the Lean setup minimal unless the project owner requests changes.

## GitHub Markdown math

When editing Markdown documentation (especially `docs/journal.md`):

- Use `$...$` for inline LaTeX, e.g. `$N=2^n$`.
- Use fenced `math` blocks for display equations, as this renders correctly on GitHub:

~~~markdown
```math
\mathbb{E}[T] = \frac{N(N-m+2)}{2m(N-m+1)}
```
~~~

- Do not use a lone `$` on separate lines for display math; GitHub rendered that literally in this repository.
- Distinguish machine-checked Lean proofs from numerical tests and unproved mathematical assumptions.
