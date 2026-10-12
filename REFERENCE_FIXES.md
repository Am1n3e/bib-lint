# Reference fixes and review decisions

> **Independent review:** Two web-search reviewers confirmed some proposals and
> challenged others. Read the [consolidated review](review-agents/README.md) before
> implementing this checklist. In particular, REF-02's automatic version/year choice,
> REF-03/06's version-conflict explanations, REF-04/07's severity, and REF-08's
> last-two-author-only correction require refinement. The recommendations below
> are historical proposals; the recorded decisions below supersede them.

Updated: 2026-09-26. Scope: all **52 used references** from the completed audit;
95 unused references are excluded. The agent review found 44 correct within the
checked fields, 1 confirmed error, 2 partial author-list matches, and 5 cases needing
review. A partial match or unavailable website is **not** a confirmed bibliography error.

Evidence: [agent review file](references.agent.json). Automated results remain in
`references.json`, unchanged. Five choices are recorded below for future fixes. No bibliography changes are applied.
Other items remain proposals. Saved automated and agent reports have not been regenerated.
All eight outstanding agent-review items are covered below. Recommendations are
recorded for the entire list; unresolved evidence is explicitly identified rather
than converted into an assumed correction.

## Recorded decisions — 2026-09-26

Documentation only, as requested. The premature bibliography edits in `cdd9cf1` were reverted. These choices supersede the earlier proposals; applying them requires a separate instruction.

| ID | Recorded choice for a future edit | Authoritative reference |
| --- | --- | --- |
| REF-02 | Refresh and store all **200 DeepSeek authors**, in source order, protecting the corporate author. The refreshed author metadata was retrieved from v2; no year or URL change was requested. This does not establish which revision the experiments used. | [arXiv v2](https://arxiv.org/abs/2501.12948v2) |
| REF-03 | Use **EMNLP 2025** using the ACL BibTeX export, preserving the citation key. Includes **Huamin Zhang**, proceedings, pages 1099–1123, DOI and publication URL. | [ACL record](https://aclanthology.org/2025.emnlp-main.58/) · [BibTeX export](https://aclanthology.org/2025.emnlp-main.58.bib) |
| REF-05 | Include all **31 AgentBay authors**, in source order. Other metadata unchanged. | [arXiv v1](https://arxiv.org/abs/2512.04367v1) |
| REF-06 | Use **TMLR, January 2026** and its publication URL. Qihan Ren follows Xuan Qi, matching the full-text author block. | [TMLR record](https://openreview.net/forum?id=CTr3bovS5F) · [paper](https://openreview.net/attachment?id=CTr3bovS5F&name=pdf) |
| REF-08 | Use **ICLR 2023**, conference entry type and publication URL. Full author sequence follows the final PDF: Jiang, Welleck, Zhou, Li, Liu, Jamnik, Lacroix, Lample, Wu. Other author-provided citation metadata differs; this is an explicit choice of the final PDF, not metadata consensus. | [ICLR record](https://openreview.net/forum?id=SMa9EAovKMC) · [final PDF](https://openreview.net/pdf?id=SMa9EAovKMC) |

Implementation status: **not applied**. The bibliography was restored to its state before these five edits. Deterministic reports, provider cache and prior agent evidence remain unchanged.

## Checklist

| ID | Citation key | Finding | Next action | State |
| --- | --- | --- | --- | --- |
| REF-01 | `lambert2024tulu` | Confirmed title encoding error | Restore missing backslash | Proposed; awaiting approval |
| REF-02 | `guo2025deepseek` | Matching truncated author list | See approved decision above | Decision recorded; not applied |
| REF-03 | `you2025datawiseagentnotebookcentricllmagent` | Author spelling differs across primary records | See approved decision above | Decision recorded; not applied |
| REF-04 | `vectifyaiPageIndex2025` | Software date lacks a verified release/commit | Identify a dated version | Review needed |
| REF-05 | `agentbay2025` | Matching truncated author list | See approved decision above | Decision recorded; not applied |
| REF-06 | `gao2025selfevolving` | Author order differs between preprint metadata and journal paper | See approved decision above | Decision recorded; not applied |
| REF-07 | `rahman2023maintenance` | Publisher page could not be fetched | Obtain primary metadata/full paper | Evidence needed |
| REF-08 | `jiang2023draft` | Conference paper and arXiv disagree on final author order | See approved decision above | Decision recorded; not applied |

## REF-01 — Tülu title encoding

- [ ] Approve and apply the one-character correction; rebuild and inspect the rendered reference.
- **Entry:** [`lambert2024tulu`, references.bib:1](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:1).
- **Issue:** `T{"u}lu` contains a literal quote. The LaTeX umlaut command requires a backslash.
- **Evidence:** [Ai2 announcement](https://allenai.org/blog/tulu-3-technical) uses **Tülu**;
  [arXiv](https://arxiv.org/abs/2411.15124) confirms the paper, authors and 2024 initial submission,
  but uses the unaccented spelling **Tulu** in its metadata.
- **Proposed replacement:**

```bibtex
title = {T{\"u}lu 3: Pushing Frontiers in Open Language Model Post-Training},
```

Only add the missing backslash. A remaining comparison between correctly encoded
**Tülu** and arXiv's **Tulu** is a source spelling variant, separate from this malformed accent.

## REF-02 — DeepSeek-R1 author truncation and version

- [ ] Decide whether to retain `and others` or replace it with the complete ordered list.
- [ ] If needed, make the cited preprint revision explicit.
- **Entry:** [`guo2025deepseek`, references.bib:8](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:8).
- **Evidence:** [arXiv v2](https://arxiv.org/abs/2501.12948v2).
- **Finding:** The 11 supplied names match the v2 prefix. The omitted names prevent a
  complete-list match, but do not establish an error. Initial submission was in 2025;
  v2 was revised in January 2026. Earlier-version search snippets have a different order.
- **Recommendation discussed:** Replace `and others` with the complete ordered author
  list from arXiv v2 and pin the URL to `https://arxiv.org/abs/2501.12948v2`.
  Keep `year = {2025}` as the initial-publication year; make the January 2026 revision
  explicit through the versioned URL rather than silently changing the citation year.
- **Reason:** Keeping all authors in the bibliography preserves attribution and enables
  complete verification. Let the ICLR bibliography style determine display abbreviation.
  Do not mix the author order from v1 with metadata from v2.
- **State:** Recommendation recorded; bibliography edit not yet approved or applied.

## REF-03 — DatawiseAgent: Huaming versus Huamin

- [ ] Resolve the author spelling against the intended cited version before editing.
- **Entry:** [`you2025datawiseagentnotebookcentricllmagent`, references.bib:2019](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2019).
- **Evidence:** [arXiv record](https://arxiv.org/abs/2503.07044) lists **Huaming Zhang**;
  [EMNLP paper](https://aclanthology.org/2025.emnlp-main.58.pdf) prints **Huamin Zhang**.
- **Proposal:** The existing spelling matches the cited arXiv metadata. Do not label
  it definitively wrong. If adopting the EMNLP version, verify the author spelling
  and update venue, URL and other publication metadata together.
- **Recommended next step:** Compare the final EMNLP author block and citation export.
  If adopting that published version, use its verified spelling and publication
  metadata as one consistent replacement. If retaining the arXiv version, retain
  Huaming and document the conflict until stronger evidence resolves it.
- **Completion check:** The chosen version, author spelling, venue and identifier
  agree; the evidence file explains why the other spelling was not selected.

## REF-04 — PageIndex software citation

- [ ] Identify the actual release, tag or commit used and verify its date.
- [ ] Add the version-specific URL and an accurate access date where supported by the bibliography style.
- **Entry:** [`vectifyaiPageIndex2025`, references.bib:2055](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2055).
- **Evidence:** [owner repository](https://github.com/VectifyAI/PageIndex/).
- **Finding:** Project identity is confirmed, but the changing live README does not
  establish the citation's 2025 date or the version used in the paper.
- **Proposal:** Bind the citation to a verified software version. Do not invent a
  release date or assume today's README describes the version used in the experiments.
- **Recommended next step:** Establish whether the paper cites PageIndex as background
  or as software actually used. For software used, recover the revision from experiment
  records. For background discussion, select a dated revision supporting that discussion.
  Verify its title, organization and date, then record the revision URL and access date.
- **Completion check:** The link identifies a stable revision and the year is supported
  by that revision's history. If the revision used cannot be recovered, document that
  limitation instead of assigning an arbitrary commit.

## REF-05 — AgentBay author truncation

- [ ] Decide whether to retain `and others` or expand to the complete author list.
- **Entry:** [`agentbay2025`, references.bib:2202](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2202).
- **Evidence:** [arXiv record](https://arxiv.org/abs/2512.04367).
- **Finding:** The ten named authors match the beginning of the 31-author record.
  Title and December 2025 submission agree. This is a partial match, not a confirmed mismatch.
- **Proposal:** If expanding, copy the full list in source order and let the bibliography
  style control display truncation. Apply the same policy to REF-02.
- **Recommendation:** Expand to all 31 authors from the reviewed record after confirming
  the intended revision, and record its version-specific URL. Keep the 2025 initial
  publication year. This improves completeness; it does not fix an incorrect prefix.
- **Completion check:** Author count and order match the chosen revision, `and others`
  is removed, and the rendered bibliography abbreviates names according to its style.

## REF-06 — Self-evolving agents survey: version-dependent author order

- [ ] Decide whether to retain the preprint or cite the TMLR publication.
- [ ] Verify and use the author order for that specific version.
- **Entry:** [`gao2025selfevolving`, references.bib:2371](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2371).
- **Evidence:** [arXiv metadata](https://arxiv.org/abs/2507.21046) and
  [TMLR paper](https://openreview.net/pdf?id=CTr3bovS5F).
- **Finding:** The arXiv metadata matches the existing list, placing Qihan Ren after
  Dongrui Liu. The journal paper places Qihan Ren after Xuan Qi. The preprint was
  initially submitted in 2025; the journal paper is dated January 2026.
- **Proposal:** Pin the intended preprint revision, or update author order, year,
  venue and link consistently when adopting TMLR. Do not automatically treat a
  later publication as invalidating the preprint citation.
- **Recommended next step:** Check which version supports the discussion in the paper.
  If adopting TMLR, verify its final citation metadata and move Qihan Ren after Xuan Qi,
  use the journal's 2026 year and venue, and link to the journal record together.
  If retaining the preprint, verify the selected revision's author block and pin it;
  do not infer that every earlier revision has the current landing page's author order.
- **Completion check:** All bibliographic fields describe the same version, and the
  author order is verified against that version's paper rather than a search snippet.

## REF-07 — Application maintenance: missing independent publisher confirmation

- [ ] Retrieve the publisher record or an author-hosted copy and confirm the metadata.
- **Entry:** [`rahman2023maintenance`, references.bib:2511](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2511).
- **Primary link:** [IEEE DOI](https://doi.org/10.1109/ACCESS.2023.3320941).
- **Finding:** The automated run resolved publisher-registered metadata, but the
  publisher page could not be fetched during the separate web review.
- **Proposal:** Check authors, title, IEEE Access volume 11, year 2023 and pages
  107068–107084. No concrete metadata correction is established yet; a fetch failure
  does not justify changing the entry.
- **Recommendation:** Leave the bibliography unchanged while obtaining independent
  primary evidence. Retry the publisher page or locate an author-hosted accepted paper.
  If the fields agree, close this item as verified without an edit; otherwise record
  the exact discrepant field and its source before proposing a correction.
- **Completion check:** Attach the accessible primary evidence and comparison result.
  Do not close the item merely because a network request eventually succeeds.

## REF-08 — Draft, Sketch, and Prove: conference author order

- [ ] Confirm the official conference author order and align the citation with it.
- **Entry:** [`jiang2023draft`, references.bib:2566](/Users/dev/workspace/research/skill.nb-iclr27/references.bib:2566).
- **Evidence:** [ICLR paper](https://openreview.net/pdf/cfd03f19d20263d9c1d1cc026a2b3528392fc857.pdf)
  and [arXiv record](https://arxiv.org/abs/2210.12283).
- **Finding:** The conference paper's author block ends **Lacroix, Lample, Wu**;
  arXiv metadata and the current entry end **Lacroix, Wu, Lample**.
- **Proposal:** Verify the final conference record before swapping the last two
  authors. Keep **2023** for an ICLR 2023 proceedings citation; the 2022 preprint
  posting alone is not a reason to change that year. Prefer the conference link
  if citing the conference version.
- **Recommendation:** Because the entry already names ICLR, align it with the final
  ICLR paper. Once the final record confirms the observed order, change the ending
  from `Lacroix and Wu and Lample` to `Lacroix and Lample and Wu`, retaining full names
  and accent encoding. Replace the preprint URL with the verified conference record.
  If the conference metadata conflicts with its PDF, retain this as a review item.
- **Completion check:** The full author sequence matches the final conference paper,
  the venue/year remain ICLR 2023, and the reference link identifies that publication.

## Validator follow-ups — not bibliography corrections

These should be handled in Bib-Lint without changing valid references to satisfy a false positive.

- [ ] **LINT-01: Strip source markup before title comparison.** `leotta2016robula`
  is flagged because Crossref returns `<scp>Robula+</scp>`. The
  [Wiley record](https://onlinelibrary.wiley.com/doi/abs/10.1002/smr.1771)
  supports the bibliography title. Do not insert `<scp>` into the BibTeX title.
- [ ] **LINT-02: Preserve publication/version context in comparisons.** Examples:
  [ST-WebAgentBench v4](https://arxiv.org/abs/2410.06703v4) supports May 2025;
  [You Only Look at Screens](https://arxiv.org/abs/2309.11436) has a June 2024 revision;
  [TroVE's ICML record](https://proceedings.mlr.press/v235/wang24az.html) supports
  Wang–Neubig–Fried, despite a different arXiv author order. Compare equivalent
  versions before proposing year, DOI or author-order replacements.
- [ ] **LINT-03: Distinguish valid accent variants from broken TeX.** After REF-01,
  Ai2's accented name and arXiv's unaccented title still differ. Record that explicit
  source variant without globally erasing accents or silently repairing malformed input.

## Independent review — 2026-09-26

Two independent agents challenged these proposals using web searches and primary
sources. Together they covered REF-01–08 and LINT-01–03, plus spot checks of
ST-WebAgentBench, You Only Look at Screens and TroVE. They did not repeat the entire
52-reference audit. **The qualifications below supersede conflicting recommendations
in the original sections above; they do not constitute approval to apply edits.**

Reports: [authors and versions](review-agents/versions-review.md),
[evidence and validator findings](review-agents/evidence-review.md), and
[consolidated review](review-agents/README.md).

### Findings by reference

| Item | Review outcome | Updated recommendation and evidence |
| --- | --- | --- |
| REF-01 — Tülu | Confirmed | Restore the missing backslash. [Ai2](https://allenai.org/blog/tulu-3-technical) supports the accented spelling; arXiv's unaccented title remains a separate source variant. |
| REF-02 — DeepSeek | Prefix confirmed; version/year recommendation challenged | Expansion is optional. Establish the revision actually cited before selecting [v2](https://arxiv.org/abs/2501.12948v2). Distinguish the 2025 initial posting from the January 2026 revision; withdraw automatic v2 adoption and an unconditional 2025-year prescription. |
| REF-03 — DatawiseAgent | Original explanation challenged | The [arXiv v2 author block](https://arxiv.org/html/2503.07044v2) also says **Huamin**, agreeing with the [ACL record](https://aclanthology.org/2025.emnlp-main.58/). Its landing metadata says Huaming. This is a conflict within the same revision, not just across venues. Huamin has stronger support for the camera-ready paper; retaining arXiv does not settle it. |
| REF-04 — PageIndex | Severity challenged | [Owner commit history](https://github.com/VectifyAI/PageIndex/commit/14a05acba15eec1f5dea74cb779bf69f294032ea) establishes a 2025 revision. The exact version used remains unknown. Pinning is a reproducibility improvement, not a demonstrated repair for a background citation. Do not assume this discovered commit was used in experiments. |
| REF-05 — AgentBay | Confirmed as optional completeness work | The ten-name prefix matches the [31-author record](https://arxiv.org/abs/2512.04367v1). Only v1 was listed at review time. Expand if desired; retaining deliberate truncation is not an incorrect author list. |
| REF-06 — Survey | Original explanation challenged | The [arXiv v4 full text](https://arxiv.org/html/2507.21046v4) agrees with TMLR: Qihan Ren follows Xuan Qi. Landing metadata differs. Pinning v4 alone does not validate the existing order. Use the chosen paper's author block and document the conflict. |
| REF-07 — IEEE Access | No correction established | Fresh [publisher-deposited Crossref metadata](https://api.crossref.org/works/10.1109/ACCESS.2023.3320941) matches the requested fields. Independent publisher-page/PDF access remains unavailable. Leave the bibliography unchanged unless discrepant primary evidence emerges; this is an access limitation, not a proven metadata error. |
| REF-08 — Draft, Sketch, and Prove | Conflict confirmed; narrow fix challenged | The [official PDF](https://openreview.net/pdf?id=SMa9EAovKMC) and [author-provided citation](https://huggingface.co/datasets/wellecks/minif2f_isabelle/blob/main/README.md) disagree on middle positions as well as the last two authors. Compare the entire sequence before editing; swapping only the last two names does not establish consensus. Keep 2023 for the conference citation. |

### Validator review

- **LINT-01 confirmed:** Remove recognized formatting tags from comparison values,
  preserving raw responses. ROBULA is a false mismatch, not a bibliography defect.
  Avoid stripping arbitrary `<...>` text that could represent mathematics.
- **LINT-02 confirmed with a qualification:** Record the cited version and whether
  its year refers to initial publication or revision. Do not choose whichever date
  happens to make a comparison pass. The three targeted version/proceedings spot
  checks supported the earlier findings within that scope.
- **LINT-03 confirmed with a qualification:** Explicit evidence supports Tülu/Tulu
  as a source spelling variant after the TeX repair. Do not erase all accents globally.

### Follow-ups for the agent evidence

- [ ] Add field-level evidence for venue/edition/publisher, or narrow `checked_fields`.
  The reviewers found 25 Correct entries claiming fields absent from their structured comparisons.
- [ ] Separate literal source values from adjudicated or normalized matches. Some
  `found` values currently reproduce input BibTeX formatting and are not verbatim retrievals.
- [ ] Identify the evidence mode and exact revision for each observation: search
  snippet, landing page, full-text author block, or citation export.
- [ ] Represent initial date, revision date, cited version and year basis explicitly.
- [ ] Add the new conflicting primary evidence and corrected rationale to the
  affected agent assessments before treating those assessments as settled.

**Scope of the result:** “44 Correct” means no discrepancy identified in the fields
reviewed, not complete verification of every field or the paper's scientific claims.
No bibliography, validator implementation or agent verdict changes were made by
these reviews. The deterministic report and provider cache remain unchanged.

## Completion record

For each accepted change, record its approval, exact edit, commit (if any), and
validation below. Reparse after bibliography edits; old agent evidence will be
flagged stale for changed entries and must be reviewed again. Keep the existing
automated report intact until a new run is explicitly requested.

| ID | Approved | Applied / commit | Validation |
| --- | --- | --- | --- |
| REF-01 | Pending | Not applied | Pending |
| REF-02 | Choice recorded only | Not applied | Pending implementation |
| REF-03 | Choice recorded only | Not applied | Pending implementation |
| REF-04 | Pending revision identification | Not applied | Pending |
| REF-05 | Choice recorded only | Not applied | Pending implementation |
| REF-06 | Choice recorded only | Not applied | Pending implementation |
| REF-07 | Pending primary evidence; may need no edit | Not applied | Pending |
| REF-08 | Choice recorded only | Not applied | Pending implementation |
| LINT-01 | Pending | Not applied | Pending |
| LINT-02 | Pending | Not applied | Pending |
| LINT-03 | Pending | Not applied | Pending |
