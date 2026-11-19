# Before releasing this draft on Zenodo

This file is for the paper author; it is not a PhD handover.

- [ ] Confirm **paper authors**, author order, affiliations, ORCIDs, contact email (as appropriate). The current manuscript intentionally contains an author placeholder; the software's copyright notice does not automatically establish manuscript authorship.
- [ ] Review the entire five-page paper for accuracy, novelty, scope, and plagiarism; review citations in the final PDF.
- [ ] Run `python -m unittest discover -s tests -v` from a **clean checkout of the full GitHub repo**, recording version and stdout/stderr.
- [ ] Run `lake -d lean build` from a clean checkout (Lean 4 toolchain as specified by the repository) and record result. If unavailable, do not claim a fresh build.
- [ ] Run the benchmark example on the frozen release commit and match the 420 raw records, report any platform-dependent float variation.
- [ ] Decide whether to make the GitHub repository public or separately publish the **relevant Lean and Python source** with Zenodo. This package's code snapshot excludes Lean proofs.
- [ ] Create a tagged, immutable source release, and record the exact Git commit SHA in the paper's data availability statement.
- [ ] Choose a paper license and check figures, code licensing, and any third-party content. MIT covers the code snapshot but not automatically the manuscript.
- [ ] Review the **Declaration of generative AI use** at the **very end of the manuscript**, confirming its scope and details are accurate; retain human responsibility for all scientific claims.
- [ ] Add definitive archive/release URL and DOI(s) to the final paper **after** IDs are assigned; update the PDF and source consistently. Zenodo assigns a DOI upon publication.
- [ ] Upload a PDF, editable source/figures, and necessary reproducibility material under appropriate access settings. Do not promise public repository access while it remains private.
- [ ] Consider including the source files `lean/FirstHitSum.lean` and its imports in the deposited supplementary material to make the formal result independently inspectable.
- [ ] Publish only after the checklist is complete; Zenodo deposit is not peer review.

**Scientific caveat:** The reported 420 runs are small selected graphs and seeded replicates, not hundreds of independent random graph problems. They support descriptive, not inferential, conclusions.
