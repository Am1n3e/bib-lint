# Sources and discovery

Default verification runs six independent providers: `arxiv`, `pmlr`, `jmlr`, `acl_anthology`, `neurips`, `openreview`. No live Crossref, OpenAlex or Semantic Scholar adapter remains. Old reports and cached responses from these sources remain readable and are not migrated or renamed.

| Provider | Direct lookup | Discovery without a URL | Source hosts |
| --- | --- | --- | --- |
| arXiv | Abstract URL or versioned/unversioned arXiv identifier | Official Atom title queries with bounded pagination | export.arxiv.org, arxiv.org |
| PMLR | Paper URL; `pmlr`/`pmlr_id` such as `v267/example25a` | Official volume index routed by year and venue, then title shortlist | proceedings.mlr.press |
| JMLR | Paper URL; `jmlr`/`jmlr_id` such as `v26/25-001` or older `volume2/example` | Official volume/year catalogs and title shortlist | jmlr.org, www.jmlr.org |
| ACL Anthology | Paper URL; `acl`, `acl_id`, `anthology_id` or `acl_anthology`; modern or older `P19-1001` IDs | Official event/volume catalogs routed by venue/year, then title shortlist; source BibTeX fallback | aclanthology.org |
| NeurIPS | Paper URL; `neurips`/`neurips_id` proceedings path | Official year proceedings catalogs and title shortlist | proceedings.neurips.cc, papers.nips.cc |
| OpenReview | Public forum URL; `openreview`, `openreview_id` or `forum` ID | Public title search, configured venue/year discovery, bounded older API fallback | openreview.net, api2.openreview.net, api.openreview.net |

Archive-specific identifiers can also be supplied as `eprint` with the corresponding `archiveprefix` (ACL uses `acl`). Unsupported URLs are not fetched; providers still discover from usable fields. Article PDFs, DOI resolver redirects and general search services are not discovery paths. DOI values can support identity when returned by an approved source.

Publication archive discovery normally needs a year or volume locator. A numeric `volume` routes PMLR/JMLR directly to their volume catalogs; an Anthology collection such as `2025.acl-long` routes ACL directly to its volume catalog. Known venue aliases improve routing; generic year catalogs can still be searched within budgets. Available adjacent years are inspected to avoid treating input years as verified source facts. Every outcome records the actual scopes and strategies. Missing routing context or request/page/candidate limits produce an explicit `incomplete_search` source diagnostic. An empty scoped search is not proof that a paper does not exist, and partial searches alone do not confirm correctness or metadata discrepancies.

Default per-entry/provider limits and extension instructions are documented in [providers.md](providers.md). arXiv is authoritative for preprints; supported archives for their publication records. Preprint/publication conflicts remain review cases, and duplicate hosting is corroboration rather than a majority vote.

OpenReview initially qualifies ICLR, ICML, NeurIPS and TMLR main venue series. Structured accepted venue IDs or supported public decision notes establish acceptance; hosting alone does not. Submitted, rejected, withdrawn and unknown-status records retain that status and cannot confirm conference publication. Anonymous authors and absent publication years remain unknown. Submission/update/acceptance timestamps are retained as provenance, not substituted for publication year. No credentials are needed or requested; inaccessible public endpoints remain source failures.

Provider descriptors, revisions and policies are recorded under schema-3 `verification_run.providers`, with protocol version 1, orchestration version 2 and comparison policy 5. Source-set, revision or policy changes invalidate saved decisions for the whole run. Raw checksum-valid evidence remains reusable under its original source ID; the previous final remains available until replacement completes. Manual reviews keep their independent entry-fingerprint bindings.

Commands remain `bib-lint verify references.bib --output audit` and `bib-lint view audit`. Without AUX, all eligible entries are checked and usage stays unknown. With `--aux paper.aux`, verification is limited to cited entries. The local UI uses the same workflow, key selection, refresh and resume rules.
