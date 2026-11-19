# Dyadic sampling/QAOA research note — source and reproducibility files

**Status:** Draft, 20 November 2026. This is a working paper, **not** a published or peer-reviewed article. The author name/affiliation, final independent verification, and Zenodo DOI are pending. The final paragraph of the manuscript is a **Declaration of generative AI use**.

The editable paper is [`source/dyadic_qaoa_note.tex`](source/dyadic_qaoa_note.tex). This folder keeps paper materials separate from the existing flat [`src/`](../src/) layout and [Lean proofs](../lean/). It is not the PhD handover.

## Files

- `source/dyadic_qaoa_note.tex`: five-page technical research-note source (including the AI-use clause after the references).
- `source/plot_results.py`: produces PDF and PNG versions of both figures and rebuilds the summary CSV.
- `source/verify_math.py`: finite enumeration and analytic QAOA consistency checks against **the repository's own Python sources**; not a replacement for Lean verification.
- `results/qaoa_benchmark_raw.csv`: 420 raw benchmark records (5 MaxCut graphs, 3 starts, 12 seeds per randomized method).
- `results/qaoa_benchmark_summary.csv`: descriptive aggregate statistics.
- `RELEASE_CHECKLIST.md`: final publication tasks for the human author.
- `VERIFICATION_LOG.txt`: verification notes from preparation of this draft; **not** a fresh clean-checkout Lean build or repository-wide CI result.
- `ZENODO_METADATA_DRAFT.md`: proposed upload metadata with placeholders (not a DOI).

The generated `figures/*.pdf`, `figures/*.png`, and compiled manuscript PDF are **build artifacts**, not tracked here. Generate them from the tracked CSV and plotting script before compiling the paper. No `code_snapshot/` duplicates are tracked in this repository, because the source modules already live in `src/`, `examples/`, and `tests/`.

## Reproduce with Python 3.11+

From the **repository root**:

```bash
python -m unittest discover -s tests -v
python examples/benchmark_qaoa_optimizers.py --csv paper/results/reproduced.csv
python paper/source/verify_math.py
```

`results/reproduced.csv` should match the checked-in raw CSV up to platform-dependent floating-point differences; use a numerical comparison if bytewise equality fails. Exact energy evaluations are not quantum hardware shots. These experiments deliberately use small, fixed MaxCut instances and retrospective targets derived from an **uncharged 16×16 offline reference grid**.

To rebuild graphics and PDF, install **matplotlib** (only needed for figures) and a TeX distribution with `pdflatex` and the standard packages named in the manuscript:

```bash
cd paper
python source/plot_results.py
pdflatex -interaction=nonstopmode -halt-on-error source/dyadic_qaoa_note.tex
pdflatex -interaction=nonstopmode -halt-on-error source/dyadic_qaoa_note.tex
```

The compiled result is `paper/dyadic_qaoa_note.pdf`. The LaTeX file references `figures/sieve_orders.pdf` and `figures/target_hits.pdf`, which the plotting script generates.

For Lean verification, from the repository root:

```bash
lake -d lean build
```

The original mathematical result is the Lean-verified **integer sum identity** for the original dyadic order (under its assumptions); the expectation follows mathematically. A fresh Lean build was **not** completed in the paper-preparation environment. Do not claim a quantum speedup, superiority of bit-reversal sampling, or hardware-shot savings based on these results.

**No Zenodo upload, DOI creation, or repository visibility change is part of these source files.**
