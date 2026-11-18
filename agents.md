# Agent notes

For related SDK documentation, VQA examples, and neighboring repositories, see [docs/neighbors.md](docs/neighbors.md).

Keep `src/` flat and the Lean setup minimal unless the project owner requests changes.

## Mathematics in GitHub Markdown

Use GitHub-compatible LaTeX notation in Markdown files such as [docs/journal.md](docs/journal.md):

- For inline math, use `$...$`, for example `$N=2^n$`.
- For displayed equations, prefer a fenced `math` block. This format is confirmed to render correctly on GitHub in this repository.
- Do **not** put a lone `$` on each line around a multiline equation: GitHub displays that literally instead of rendering the equation.

Example of the preferred display-math syntax:

~~~markdown
```math
\mathbb{E}[T] = \frac{N(N-m+2)}{2m(N-m+1)}
```
~~~

Keep proof-status claims precise: distinguish identities proved in Lean from numerical checks and conjectured connections to the actual dyadic sieve.
