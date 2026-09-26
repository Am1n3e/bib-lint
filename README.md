# bib-lint

Parse BibTeX, identify used references from compiled AUX, and compare citation
metadata across providers. BibTeX and AUX inputs are never modified.

## Run and resume

Requires [uv](https://docs.astral.sh/uv/). From this project directory:

```sh
uv sync
uv run bib-lint parse ../skill.nb-iclr27/references.bib \
  --aux ../skill.nb-iclr27/.out/iclr2027_conference.aux \
  --output references.json
uv run bib-lint verify references.tmp.json
```

`parse` writes **references.tmp.json**, reserving `references.json` for the completed
verification report. Without `--output`, files are placed beside the bibliography.
`--output references.tmp.json` also works. `--include-source` includes decoded
BibTeX source text, and `--encoding` changes the default UTF-8 input encoding.

`verify` checks only entries with `validations.is_used: true`. All entries remain
in the report; unused ones are skipped. Missing usage information is an error:
parse with `--aux` before verifying. Use freshly compiled AUX files; the parser
cannot detect whether the AUX is stale.

To verify one used reference by citation key:

```sh
uv run bib-lint verify references.tmp.json --key lambert2024tulu
```

Key matching is case-insensitive; missing, ambiguous, or unused keys produce an
error before modifying the report. Add `--refresh --verbose` to fetch that reference
again and show responses. Other compatible verification results are preserved.
If other used references are still pending, the report stays in `.tmp.json`;
the final rename occurs only after all used references have completed lookups.

For every used reference the terminal shows each provider's fetch, outcome, and
retry delays, followed by:

```text
Verifying 1/51: example
  crossref: Fetching ...
  crossref: Found
  semantic_scholar: Fetching ...
  semantic_scholar: Rate limit backoff 2 seconds
  semantic_scholar: Found
  status: correct
  found: 2/2
  consensus: 2/2
```

`found` counts unambiguous records over applicable methods. `consensus` counts
agreement over **found records only**. An unavailable provider is neither a found
record nor a vote against the consensus. No found records means `0/0`.

Every completed method is saved atomically into `references.tmp.json`. A stable
`references.json.lock` sidecar protects the whole run, including every checkpoint
write and final rename. A second writer fails clearly rather than interleaving
updates. Locks are advisory and released automatically when the process exits;
the sidecar remains to preserve its inode. This implementation uses POSIX `flock`
(macOS/Linux).

To resume after interruption, run the same `verify` command again. It skips saved
successful/no-result/ambiguous/inapplicable lookups and retries saved errors. A
method interrupted before it returned is fetched again. Input fingerprints,
method registry, and policy versions prevent reusing incompatible decisions.
Parsing refuses to overwrite a verification checkpoint; resume it instead.

Once every applicable method has been attempted for every used reference, the
checkpoint is atomically renamed to `references.json`. A prior final report stays
unchanged until then. Finishing a run does not mean every reference was verified:
errors and unresolved cases remain explicit. Repeating the command after completion
also works and retries errors from the final report. `--refresh` reruns all methods
and bypasses response-cache reads. `--output` can select another final filename.

Use `--verbose` to print every HTTP response, including unsuccessful retry attempts
and cached responses. Output includes URL, attempt, status, headers, and the complete
body. JSON responses are pretty-printed. XML and HTML bodies are printed directly,
with their original line breaks, after a plain-text metadata header. Other plain-text
bodies remain JSON strings without truncation. Network failures have an error object
and no HTTP status.
Known API credentials and cookie headers are redacted. Legacy flat cache files are no longer read; fresh requests populate the new layout.

```sh
uv run bib-lint verify references.tmp.json --verbose --refresh
```

`--verbose` alone does not rerun completed methods; combine it with `--refresh`
to see fresh responses for every used reference.

## JSON structure

```json
{
  "summary": {"total_count": 1, "total_not_used": 0},
  "items": [
    {
      "entry": {"key": "example", "type": "book", "fields": {"title": "Example"}, "persons": {}},
      "validations": {"is_used": true}
    }
  ],
  "schema_version": 2,
  "source": {"name": "references.bib", "sha256": "..."},
  "preambles": []
}
```

Without AUX, `total_not_used` is `null` and `validations` is `{}`. With AUX, usage
recognizes `\citation{...}`, `\nocite{*}` through `\citation{*}`, and recursive
`\@input{...}` records. It ignores `\bibcite`, follows included paths from the root
AUX directory (with an including-directory fallback), and detects cycles. It does
not execute TeX. Biblatex AUX is explicitly unsupported. Missing citation keys are
reported in the terminal. Missing included files or malformed records fail parsing.

Verification adds `validations.correctness` containing:

- `is_correct`: `true`, `false`, or `null` (unresolved); no duplicate overall status.
- `methods`: each provider's `name`, lookup `status`, `found_ref`, comparisons,
  differences, source URL, request evidence, and timestamps. Ambiguous and rejected
  candidates remain visible.
- `consensus`: agreement over found records, applicable method count, and separate
  counts for failures, no results, ambiguity, disagreement, and inapplicability.
- `canonical_ref`, decision `reason`, `policy_version`, and checked fields/scope.
- `complete`: whether all method outcomes are available for that entry. Partial
  checkpoints leave `is_correct` as `null` until all methods have returned.

The report's `verification_run` stores resume metadata and completion state.
`summary.verification` counts correct, incorrect, unresolved, method errors, and
skipped unused entries. Report generation succeeds even with provider errors
(exit 0); input/write failures exit 2, and keyboard interruption exits 130.

## Verification methods and policy

Every registered adapter runs independently, even when another succeeds or fails:

| Adapter | Lookup |
| --- | --- |
| `verify_reference_crossref` | DOI, then bibliographic search if identity is not established |
| `verify_reference_arxiv` | arXiv identifier, then title search |
| `verify_reference_openalex` | DOI, then title search |
| `verify_reference_semantic_scholar` | DOI/arXiv identifier, then title search |
| `verify_reference_publisher` | Citation meta tags on supported input landing-page URLs |

Publisher hosts: PMLR, JMLR, ACL Anthology, and NeurIPS proceedings. Absent or
unsupported landing-page URLs are `not_applicable`; the adapter does not discover
publisher URLs or resolve DOI URLs. This registry is extensible, not exhaustive
coverage of scholarly APIs. Crossref, arXiv, and supported publisher records are
primary metadata sources; OpenAlex and Semantic Scholar are corroborating indexes.

Identifiers alone cannot establish identity when the title is unrelated. Search
matches require close titles and overlapping author surnames. Title, ordered
authors, year, venue, and supplied identifiers are compared conservatively.
Compatible initials, abbreviated venues, missing fields, and near-matching titles
remain unresolved. A venue absent from the input is not checked. Core citation
checks do not validate pages, volume, edition, citation style, or claim support.

An authoritative cluster takes precedence over indexes. Conflicting authoritative
records, ambiguous searches, and preprint/publication differences require review.
Index agreement alone cannot establish correctness. `false` requires a confirmed
field discrepancy; `true` requires checked fields to match; insufficient evidence
produces `null`. Multiple queries to a provider count as one method.

Optional environment variables: `CROSSREF_MAILTO`, `OPENALEX_API_KEY`, and
`SEMANTIC_SCHOLAR_API_KEY`. Public endpoints are attempted without credentials;
access errors remain visible. Provider docs:
[Crossref](https://www.crossref.org/documentation/retrieve-metadata/rest-api/),
[arXiv](https://info.arxiv.org/help/api/user-manual.html),
[OpenAlex](https://help.openalex.org/api/),
[Semantic Scholar](https://api.semanticscholar.org/api-docs/graph).

Responses are stored under `.bib-lint-cache/` (`--cache-dir` relocates it):

```text
.bib-lint-cache/
  checksum.json
  checksum.json.lock
  lambert2024tulu/
    arxiv_1780000000000000000.xml
    crossref_1780000000000000001.json
    publisher_1780000000000000002.html
```

Filenames use the method and a nanosecond timestamp. Unsafe citation-key characters
are URL-encoded so keys cannot escape their directories. Bodies are saved as the
original HTTP entity bytes supplied by the HTTP client, without JSON reserialization,
pretty-printing, redaction, or XML/HTML conversion. HTTP transport compression is
already decoded by the client. Plain-text responses use `.txt`.

`checksum.json` lists each relative file path and its SHA-256, citation key, method,
request identity, status, encoding, retrieval time, and response metadata. The manifest
and response writes share a file lock. Successful responses are reusable for seven days;
failed responses and retries are also archived, but never reused as successful results.
Every cache read verifies the stored bytes against the manifest. A mismatch or missing
checksum/file invalidates and removes that entry, then fetches and records a replacement.
Untracked response files are removed on access. A failed replacement fetch is reported
as a provider error; the corrupted response is never returned.

Manifest URLs exclude API keys. Raw bodies are deliberately unaltered; terminal verbose
output still redacts credentials. Evidence records include raw file paths and checksums.
Checksums detect changes relative to the manifest; they are not signatures authenticating
both files and the manifest against coordinated modification. Legacy flat cache files
are ignored rather than trusted or automatically deleted.

Requests have 20-second timeouts and per-provider pacing
(3.1 seconds for arXiv, 1 second otherwise). Semantic Scholar retries transient failures after 10, 15, 20, 25, and 30 seconds
(six attempts total). A numeric `Retry-After` can increase these delays up to
30 seconds; longer delays stop retries and report unavailability. Other providers
retry after 2 then 4 seconds (three attempts total), honoring numeric `Retry-After`
up to 10 seconds. Jitter and HTTP-date Retry-After are not
implemented. Backoff messages appear as they happen.

## Python API and code layout

```python
from bib_lint import parse_bib, parse_file, parse_string
from bib_lint.verification import verify_file

bib_result, aux_result = parse_bib("references.bib", "paper.aux")
output, summary = verify_file(bib_result.output)
```

- `parser.py`, `models.py`: pure BibTeX parsing and serializable data.
- `aux.py`: pure AUX citation extraction.
- `workflow.py`: parsing coordination and initial checkpoint creation.
- `storage.py`: atomic writes and shared report locking.
- `verification/providers.py`: independent method adapters.
- `verification/matching.py`, `consensus.py`: matching and decision policy.
- `verification/http.py`: HTTP, pacing, retries, and progress events.
- `verification/cache.py`: raw responses, checksum manifest, and verified cache reads.
- `verification/__init__.py`: `verify_reference` and resumable `verify_file`.
- `cli.py`: arguments and terminal presentation.

Pybtex preserves key spelling, entry order, TeX field content, structured names,
custom fields, and preambles. Macros are expanded; crossref inheritance is not
applied. Decoded original text and its source-byte hash are retained in memory;
parsed values are not a lossless syntax tree. Parsing errors include duplicate
keys/fields and undefined macros. No metadata repairs or BibTeX rewrites occur.

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv build
```

## Streamlit viewer

```sh
uv run bib-lint view references.tmp.json
# Or view a completed report:
uv run bib-lint view references.json
```

Open http://127.0.0.1:8501. Use `--port` or `--cache-dir` to change defaults.
The sidebar lets you choose the report/cache paths and reload a running checkpoint.
A checkpoint path automatically falls back to its final report after verification
renames it. The viewer binds to localhost and only reads report and cache files.

The overview includes **all** references with citation key, usage, correctness,
found/applicable ratio, consensus/found ratio, distinct discovered URLs, and a note.
Click a table cell to open the reference detail page; use the table's native search,
sort, and column controls as needed. Unverified entries remain visible as pending
or not checked, rather than being marked incorrect.

Details use native Streamlit tabs:

- **Comparison:** provider outcomes, differences and unresolved field comparisons,
  plus confirmed correction proposals supported by authoritative evidence. Matching
  fields can be included. Proposals never edit the bibliography.
- **Cached responses:** select any saved call for that citation, including retries
  and failures. SHA-256 is verified before displaying or downloading it. JSON and
  XML are pretty-printed; HTML is displayed as source without executing it. The
  download preserves original bytes. Corrupted evidence is refused, not changed.
- **Your entry:** the parsed bibliography entry.

Built entirely with Streamlit's built-in components; no custom HTML, CSS, or JS UI.
