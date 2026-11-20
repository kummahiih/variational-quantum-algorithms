# Before releasing this draft on Zenodo

This file is for the paper author; it is not a PhD handover.

- [x] Set the paper author to **Pauli Rikula**, with **no affiliation** listed (as requested).
- [ ] Confirm any optional ORCID or contact email for Zenodo metadata; do not invent affiliations or identifiers.
- [ ] Review the entire five-page paper for accuracy, novelty, scope, and plagiarism; review citations in the final PDF.
- [x] Author ran `python -m unittest discover -s tests -v` from the repository: **29 tests passed**; terminal output supplied on 20 November 2026. (Not independently repeated on a clean release checkout.)
- [x] Author ran `lake -d lean build` from the repository: **Build completed successfully (19 jobs)**; terminal output supplied on 20 November 2026. (Not independently repeated on a clean release checkout.)
- [ ] Repeat the full test suite, Lean build, and benchmark against the **final tagged clean checkout**; record tool versions and compare the 420 benchmark rows (allow for stated floating-point differences).
- [ ] Confirm the repository and relevant Lean/Python sources are publicly accessible when the Zenodo record is published.
- [ ] Create a tagged, immutable source release, and record the exact Git commit SHA in the paper's data availability statement.
- [ ] Choose a paper license and check figures, code licensing, and any third-party content. MIT covers the code snapshot but not automatically the manuscript.
- [ ] Review the **Declaration of generative AI use** at the **very end of the manuscript**, confirming its scope and details are accurate; retain human responsibility for all scientific claims.
- [ ] Add definitive archive/release URL and DOI(s) to the final paper **after** IDs are assigned; update the PDF and source consistently. Zenodo assigns a DOI upon publication.
- [ ] Upload the final PDF and necessary reproducibility material to Zenodo; verify the repository link works for unauthenticated readers after publication.
- [ ] Consider including the source files `lean/FirstHitSum.lean` and its imports in the deposited supplementary material to make the formal result independently inspectable.
- [ ] Publish only after the checklist is complete; Zenodo deposit is not peer review.

**Scientific caveat:** The reported 420 runs are small selected graphs and seeded replicates, not hundreds of independent random graph problems. They support descriptive, not inferential, conclusions.
