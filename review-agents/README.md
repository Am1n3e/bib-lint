# Independent challenges to the reference audit

Two agents independently used web searches and primary sources on 2026-09-26.
They reviewed all eight proposed reference items and the three validator follow-ups,
with targeted spot checks of previously accepted references. This is not a second
exhaustive verification of all 52 citations.

- [Author lists and publication versions](versions-review.md)
- [Evidence quality and validator findings](evidence-review.md)
- [Original proposed fixes](../REFERENCE_FIXES.md)

## Confirmed

- **REF-01:** The missing backslash in the Tülu title is a genuine encoding defect.
- **REF-02 / REF-05:** DeepSeek and AgentBay have matching truncated author lists.
  Expanding them is optional completeness work, not repair of an incorrect prefix.
- **LINT-01:** ROBULA's Crossref formatting tags cause a false title mismatch.
- **LINT-02 / LINT-03:** Version-aware comparison and explicit accent-variant handling
  are justified. Do not erase meaningful differences globally.
- The ST-WebAgentBench v4, You Only Look at Screens v4 and TroVE proceedings spot
  checks support the reported metadata within their stated scope.

## Recommendations challenged

| Item | New evidence / challenge | Consequence |
| --- | --- | --- |
| REF-02 | No evidence establishes that the paper used DeepSeek v2. Initial and revision years are different concepts. | Withdraw automatic v2 selection and the unconditional instruction to retain 2025 when pinning it. Establish the intended revision and state the year basis. |
| REF-03 | [arXiv v2 full text](https://arxiv.org/html/2503.07044v2) also says **Huamin**, agreeing with ACL; its landing metadata says Huaming. | This is a same-version metadata/full-text conflict, not merely a preprint/publication difference. Huamin has stronger support for the camera-ready paper. |
| REF-04 | [Owner history](https://github.com/VectifyAI/PageIndex/commit/14a05acba15eec1f5dea74cb779bf69f294032ea) establishes a 2025 PageIndex revision. | Narrow the concern to the exact version cited/used. Missing a commit is not by itself an error in a background citation. Do not substitute this discovered commit for an unknown experimental revision. |
| REF-06 | [arXiv v4 full text](https://arxiv.org/html/2507.21046v4) agrees with TMLR: Qihan Ren follows Xuan Qi. Landing metadata differs. | Pinning v4 does not validate the existing author order. Resolve against the chosen full text. |
| REF-07 | A fresh [publisher-deposited Crossref record](https://api.crossref.org/works/10.1109/ACCESS.2023.3320941) agrees with the supplied fields. Independent publisher-page/PDF access remains unavailable. | No bibliography correction is established. The remaining issue is evidence access, not evidence of incorrect metadata. |
| REF-08 | [Final conference PDF](https://openreview.net/pdf?id=SMa9EAovKMC) and author-supplied citation records disagree on middle positions as well as the last two authors. | A last-two swap does not establish full consensus. Compare the entire sequence and document which primary record is followed. |

Full links, observations and qualifications are in the two reports above.

## Agent evidence file: required improvements before treating it as exact source data

These findings concern `references.agent.json` and its presentation, not the immutable
automated report or provider cache.

- [ ] Add field-level evidence for venue/edition/publisher, or narrow `checked_fields`:
  25 of the 44 entries labelled Correct claim fields absent from their structured comparisons.
- [ ] Separate literal fetched values from adjudicated/normalized values. Several
  `found` values reproduce input BibTeX formatting and must not imply verbatim retrieval.
- [ ] Record evidence mode and exact version for each observation: search snippet,
  landing page, full-text author block, or citation export.
- [ ] Model initial publication date, revision date, cited version and year basis
  explicitly. Do not select whichever date makes the comparison pass.
- [ ] Incorporate the new conflicting primary evidence into the affected assessments.

**Qualified audit summary:** 44 entries have no discrepancy in the fields reviewed;
this is not complete field verification. One confirmed encoding repair, two optional
author-list completeness decisions, and five review/evidence questions were originally
recorded. These reviews refine the questions; they do not justify blanket status changes.

## State

No bibliography edits, validator code changes, or agent verdict changes were applied
as part of this independent review. The deterministic report and cache remain intact.
The original checklist now links here so its challenged recommendations are visible.
