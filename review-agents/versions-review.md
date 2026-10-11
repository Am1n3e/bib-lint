# Independent review: versions and author lists

Reviewed 2026-09-26. Scope: REF-02, REF-03, REF-05, REF-06, REF-08 in
`REFERENCE_FIXES.md`, their `references.agent.json` assessments, and the original
BibTeX entries. Web searches and primary records were checked independently.
No bibliography, existing review JSON, or checklist was edited.

## Findings

| Item | Verdict on proposal | Required change to proposal | Agent status |
| --- | --- | --- | --- |
| REF-02 | Challenge in part | Do not automatically select v2 or prescribe a universal initial-year convention | Keep Partial match; qualify year assessment |
| REF-03 | Challenge rationale | Conflict also exists inside arXiv v2, not only between publication versions | Keep Needs review; stronger correction evidence |
| REF-05 | Confirm | Expansion is optional completeness improvement, not repair of incorrect names | Keep Partial match |
| REF-06 | Challenge rationale | Current arXiv full text agrees with TMLR; its landing metadata is inconsistent | Keep Needs review |
| REF-08 | Confirm conflict, challenge narrow fix | More than the last two authors differs in primary citation records | Keep Needs review |

## REF-02 — DeepSeek-R1

The [v1 landing record](https://arxiv.org/abs/2501.12948v1) dates the initial
submission to 22 January 2025; the [v2 record](https://arxiv.org/abs/2501.12948v2)
dates the revision to 4 January 2026. The supplied prefix matches v2; v1 has a
different order among the five names following Junxiao Song. Thus the checklist's
matching-prefix finding is confirmed by direct records, not merely search snippets.

The proposed automatic choice of v2 goes further than this evidence supports.
We do not know which revision the paper actually discusses. Select that revision
first. Expanding `and others` is optional completeness work; it is not proof that
the existing citation is wrong. A 2025 year can identify the work's initial
publication, but is not the revision date. Do not present “pin v2 and keep 2025”
as a universally required bibliographic rule. If chosen, document both dates
explicitly and consistently; do not classify the revision-year comparison as an
unqualified match. No evidence here establishes that the paper must upgrade to v2.

**Proposed checklist wording:** Confirm the revision supporting the cited claim;
retain or expand its author list consistently. If choosing v2, record that it is
the January 2026 revision of a work first posted in 2025. Retain Partial match as
the author-completeness status until expansion is actually approved.

## REF-03 — DatawiseAgent

The [arXiv landing record](https://arxiv.org/abs/2503.07044v2) says Huaming Zhang.
However, the [same v2 full text](https://arxiv.org/html/2503.07044v2), author block
at the top, says **Huamin Zhang**. The [ACL publication record and citation](https://aclanthology.org/2025.emnlp-main.58/)
and [published PDF](https://aclanthology.org/2025.emnlp-main.58.pdf) also use Huamin.
The v2 landing page identifies itself as the EMNLP camera-ready version.

Therefore, “keep Huaming when retaining arXiv” is too strong: retaining the current
preprint does not resolve the disagreement. This is also a metadata/full-text
conflict within the same arXiv revision. The final author spelling has substantially
stronger support for **Huamin**, even without changing venue. The original v1 has
a different title; retaining an older version requires checking all its fields,
not merely using its metadata to justify a spelling.

**Proposed checklist wording:** Prefer Huamin for a citation to the current
camera-ready paper, supported by the arXiv v2 author block and ACL record. Record
the contrary arXiv landing metadata. Keep Needs review until the intended revision
and exact correction are approved; do not claim the existing landing-page match
alone validates the name.

## REF-05 — AgentBay

The [arXiv primary record](https://arxiv.org/abs/2512.04367) lists 31 authors;
the ten names in the bibliography are its ordered prefix. Its history contains
only [v1](https://arxiv.org/abs/2512.04367v1), dated 4 December 2025, at review time.
The title and year agree.

The recommendation to expand is reasonable but optional. No incorrect prefix,
date, or identity was established. The checklist need not imply unresolved revision
history here: v1 is the only listed version. A version-specific URL can be added
as provenance. Preserve Partial match if the deliberate `and others` remains.

## REF-06 — Self-evolving agents survey

The [current arXiv landing record](https://arxiv.org/abs/2507.21046v4) places
Qihan Ren after Dongrui Liu. The [arXiv v4 full text](https://arxiv.org/html/2507.21046v4),
author block at the top, instead places Qihan Ren immediately after Xuan Qi.
The [TMLR paper](https://openreview.net/pdf?id=CTr3bovS5F) uses the latter order
and identifies publication as January 2026. ArXiv v4 is dated 16 January 2026;
the work was first posted in July 2025.

The checklist correctly cautions against mixing records, but its description of
a simple preprint/journal difference is incomplete. Pinning **v4** does not make
the existing order match that revision's author block. Both full texts support
the earlier placement of Ren; the landing-page metadata is the conflicting source.

**Proposed checklist wording:** For current v4 or TMLR, use the full-text author
order with Ren after Qi, recording the contrary landing metadata. Retain the
original order only if an explicitly selected older version actually supports it.
If choosing TMLR, update venue, year (2026), and link together. Needs review remains
appropriate while the intended version is undecided.

## REF-08 — Draft, Sketch, and Prove

The [official OpenReview PDF](https://openreview.net/pdf?id=SMa9EAovKMC) confirms
ICLR 2023 and ends with Lacroix, Lample, Wu. The [arXiv metadata](https://arxiv.org/abs/2210.12283)
ends with Lacroix, Wu, Lample. The proposed final-two swap matches the PDF.

However, [coauthor Wu's publication page](https://www.cs.toronto.edu/~ywu/Publications.html),
[Google's ICLR listing](https://research.google/blog/google-at-iclr-2023/), and
[coauthor Welleck's dataset citation](https://huggingface.co/datasets/wellecks/minif2f_isabelle/blob/main/README.md)
place Lacroix fourth, followed by Liu, Li, and Jamnik, then Lample and Wu. Thus
the conflict affects the middle of the sequence too. Do not suggest the final-two
swap alone settles the full conference citation.

The OpenReview forum and public API were blocked during this independent check;
the official PDF was accessible through web search. **Keep Needs review.** Prefer
the stable conference forum URL `https://openreview.net/forum?id=SMa9EAovKMC`
over a hashed PDF URL after the full author-order decision. Keep 2023 for the
conference citation; the preprint's 2022 posting does not invalidate that year.

**Proposed checklist wording:** Compare the complete official citation export
against the final PDF and author-supplied citation. Resolve or document the
whole-order conflict before changing authors. A PDF-based correction is defensible
if stated as that source choice, but should not be presented as unanimous primary
metadata consensus.

## Review limits

This review tests the proposed metadata changes, not whether the paper's scientific
claims are supported by any version. It does not establish which revision the
authors used. Current source conflicts should be preserved in evidence rather than
silently resolved by majority vote. The separate agent JSON should gain the new
version-specific links and qualified rationale; no automatic verdict change is
required for these five entries.
