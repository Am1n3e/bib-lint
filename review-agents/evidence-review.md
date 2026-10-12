# Independent evidence challenge

Reviewed 2026-09-26. This is a fresh web-search and primary-source review of REF-01, REF-04, REF-07, LINT-01–03, and three targeted “Correct” spot checks. No bibliography, deterministic report, or agent report was changed. It is not a second exhaustive audit of all 52 entries.

## Conclusions

| Item | Verdict | Action |
| --- | --- | --- |
| REF-01 | Confirm | The missing backslash is a genuine title-encoding defect. |
| REF-04 | Challenge severity; confirm optional improvement | Primary owner history now establishes a 2025 version; exact experiment version remains unknown. Do not call a background repository citation incorrect solely for lacking a commit. |
| REF-07 | Unresolved independent full-paper access; challenge fix classification | Fresh publisher-deposited metadata agrees. No demonstrated bibliography error; this is an evidence-access limitation. |
| LINT-01 | Confirm | Strip recognized source formatting markup for comparison, retain original raw response. |
| LINT-02 | Confirm, with policy qualification | Compare the cited manifestation and distinguish initial posting from revision dates. |
| LINT-03 | Confirm, with qualification | Treat known Tülu/Tulu spelling variation explicitly; do not erase all diacritics globally. |

## REF-01 — missing TeX accent command

The original `.bib` actually contains `T{"u}lu` (no backslash). The proposed replacement `T{\"u}lu` contains one backslash and is the correct TeX accent construction. This is not just a case or capitalization disagreement. [Ai2's own announcement](https://allenai.org/blog/tulu-3-technical) and [model page](https://allenai.org/tulu) use the accented name. [arXiv](https://arxiv.org/abs/2411.15124) uses the unaccented title.

**Recommendation:** Confirm the one-character repair, subject to the user's normal approval process. Preserve the separate source spelling variation in the audit. Do not claim that the arXiv title itself proves the umlaut; Ai2 supplies that evidence. Rebuild to ensure the rendered citation contains ü and no literal quote.

## REF-04 — PageIndex date and version

The original warning was cautious, but stronger primary evidence is readily available. The owner's [commit 14a05acba15eec1f5dea74cb779bf69f294032ea](https://github.com/VectifyAI/PageIndex/commit/14a05acba15eec1f5dea74cb779bf69f294032ea) exists in the repository history. The [GitHub API query restricted to 2025](https://api.github.com/repos/VectifyAI/PageIndex/commits?until=2025-12-31T23:59:59Z&per_page=1) returns that commit with a committer date of **2025-12-22T00:26:04Z**. The [README at that revision](https://raw.githubusercontent.com/VectifyAI/PageIndex/14a05acba15eec1f5dea74cb779bf69f294032ea/README.md) describes the reasoning-based project. These establish existence of the cited project in 2025, though not its first release date or the revision used in experiments.

**Recommended revision to checklist:** Replace the broad date-uncertainty finding with “2025 project existence confirmed; exact version used not established.” Keep revision pinning as a reproducibility improvement. If this is only a background reference, absence of a tag/commit is not, by itself, a factual error. If software was actually executed in the study, recover the real revision; never substitute the convenient commit above as if it were the experimental version. An access date must be the actual inspection date, not an invented 2025 date.

## REF-07 — IEEE Access citation

Web search found corroborating indexed metadata, but these are not primary substitutes. Both the [DOI resolver](https://doi.org/10.1109/ACCESS.2023.3320941) and [IEEE record](https://ieeexplore.ieee.org/document/10267922/) still failed through the browser tool. A candidate author CV on the PAAET institutional site also failed to open, so I do not claim to have verified the paper through it.

A fresh read of the [Crossref DOI record](https://api.crossref.org/works/10.1109/ACCESS.2023.3320941) returned the publisher-deposited title, five authors in order (Hanif Ur Rahman, Asaad Alzayed, Muhammad Ismail Mohmand, Abdullah M. Albarrak, Sultan Noman Qasem), year 2023, volume 11, and pages 107068–107084. These agree with the bibliography. This is primary deposited metadata, but overlaps the deterministic source and is not a statistically independent vote.

**Recommendation:** No bibliography edit. Classify this as “metadata confirmed through publisher deposit; independent full-paper check unavailable” rather than “needs fixing.” It is reasonable to retain a review flag if the explicitly chosen review standard requires independent publisher-page/PDF access. Make that standard visible; failed HTTP access is not evidence of a wrong reference.

## LINT-01 — ROBULA markup

A fresh [Crossref request](https://api.crossref.org/works/10.1002/smr.1771) returns the title with `<scp>Robula+</scp>`. The tags specify typography, not extra title words. The [author-hosted accepted manuscript](https://tsigalko18.github.io/assets/pdf/2016-Leotta-JSEP.pdf), page 1, supplies the plain title, four authors, DOI, volume 28, issue 3, pages 177–204 and year 2016. The [authors' university project page](https://sepl.dibris.unige.it/ROBULA.php) is another primary identity source.

**Recommendation:** Confirm the validator fix and leave the bibliography unchanged. Strip recognized HTML/XML formatting in normalized comparison values only; retain immutable source bytes and raw title evidence. Do not implement an indiscriminate `<...>` regex that could delete legitimate mathematical content. Tests should cover this source title, HTML entities, genuine title differences, and literal inequality/math text.

## LINT-02 and “Correct” spot checks

1. **ST-WebAgentBench — confirmed within stated scope.** The [explicit v4 record](https://arxiv.org/abs/2410.06703v4) gives six authors in the supplied order and revision date **19 May 2025**; its initial submission is **9 October 2024**. The input explicitly points to v4, so May 2025 is defensible as the cited version date. Do not claim that 2025 is the initial publication date.
2. **You Only Look at Screens — metadata supported; pinning still optional improvement.** [arXiv history](https://arxiv.org/abs/2309.11436) shows v4 on **7 June 2024** and v1 on **20 September 2023**, with the two matching authors. The [ACL record](https://aclanthology.org/2024.findings-acl.186/) confirms a distinct 2024 proceedings manifestation. The existing June 2024 preprint date can refer to v4; it does not mean initial publication in 2024. Pin v4 if retaining that rationale. Do not overwrite the arXiv DOI with the ACL DOI while keeping the rest of the preprint citation unchanged.
3. **TroVE — confirmed.** [Official PMLR citation export](https://proceedings.mlr.press/v235/wang24az.html) explicitly supplies **Wang, Neubig, Fried**, ICML 2024, volume 235 and pages 51177–51191. This supports the existing proceedings author's order and supersedes a comparison to the differently ordered [arXiv record](https://arxiv.org/abs/2401.12869) for this specific citation. It does not establish that all manifestations must share one author sequence.

**Policy challenge:** The checklist recommends keeping initial year 2025 when pinning DeepSeek v2 from 2026, while it accepts a revision year for ST-WebAgentBench. Both approaches can be bibliographically intelligible, but the validator should explicitly model `initial_submission_date`, `revision_date`, `version`, and `cited_year_basis` rather than choose whichever date makes a comparison pass. A mere coincident revision year should not prove correctness without a link to the intended revision.

## LINT-03 — accent variants

Confirm the distinction between broken TeX and a verified spelling variant. After fixing the missing backslash, decoded Tülu and arXiv's Tulu are not literally identical. Ai2 supplies direct evidence for the accented spelling, so the checker may record a source variant or an explicitly justified equivalent. Do not silently normalize away every accent: other titles and author names may genuinely differ. This should not become a general fuzzy-match rule that changes a mismatch to “Correct” without evidence.

## Challenge to the “44 Correct” summary and evidence representation

The three targeted checks did not uncover a wrong bibliography field. They support the qualifier **“correct within the checked fields”**, not an unconditional certification of 44 complete references or of the scientific claims supported by those references.

The evidence representation needs strengthening:

- Of the 44 “Correct” items, 19 list only title/authors/year, 24 also claim venue checked, and one claims edition/publisher. **25 therefore claim checked fields absent from their structured comparisons**, which currently contain title/authors/year only. Add field-level records for venue/edition/publisher or narrow `checked_fields`.
- Several `found` values copy BibTeX formatting from the input (e.g. brace-protected TroVE and ST-WebAgentBench titles). They can represent an adjudicated normalized match, but should not be presented as exact values fetched from the source. Keep the literal source value separately and label normalization explicitly.
- Generic evidence labels such as “Primary record” and generic `access: web search / primary page` obscure whether a page was opened, only a search snippet was read, or a PDF author block was checked. Record the exact page/version and evidence mode for each checked field.
- A source URL is useful, but a field-specific note identifying the title block, author sequence, date history or citation export makes the review auditable. Do not turn web-search agreement into an extra independent majority vote when it is reading the same arXiv/Crossref metadata.

**Recommended summary wording:** “44 entries have no discrepancy in the fields reviewed; this is not complete field verification. One confirmed encoding repair, two optional author-list completeness decisions, and five review/evidence questions remain.” Update counts only after actual adjudication of the other review items; this targeted review does not justify changing all 52 statuses.
