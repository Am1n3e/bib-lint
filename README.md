# bib-lint

Audit local BibTeX metadata against independent scholarly sources, then inspect
comparisons and raw evidence in a local UI. Source bibliographies and compiled AUX
files are never edited. Requires Python 3.12+ and macOS/Linux.

Official reference benchmark harnesses, dataset versions, scoring conditions and
commands are documented in [evaluation/README.md](evaluation/README.md).

## Install as a uv tool

From any directory, using the absolute checkout path:

```sh
uv tool install /path/to/bib-lint
bib-lint --version
bib-lint --help
```

For a local installation that follows source edits:

```sh
uv tool install --editable /path/to/bib-lint --force
```

Or build and install a wheel (no package-index publication required):

```sh
cd /path/to/bib-lint
uv build
uv tool install dist/bib_lint-0.1.0-py3-none-any.whl --force
```

`--force` replaces an existing installation of this tool. These are installed
commands; development uses `uv sync` and `uv run bib-lint` inside the checkout.
Streamlit is included as a runtime dependency, so both commands work outside the
checkout. Paths resolve from your current working directory.

## Verify and view

```sh
bib-lint verify references.bib
bib-lint verify references.bib --aux paper.aux --output audits/current
bib-lint verify references.bib --output audits/current --aux paper.aux --key Smith2025
bib-lint verify references.bib --output audits/current --aux paper.aux --key Smith2025 --refresh
bib-lint verify references.bib --json --verbose
bib-lint view audits/current
bib-lint view
```

Without AUX, **every entry is eligible**, while paper citation usage remains
unknown. With `--aux`, only cited entries are checked; unused entries remain
visible as Skipped. AUX includes are read recursively without executing TeX.
Missing citation keys produce warnings. Use a freshly compiled AUX: its freshness
cannot be inferred by the parser.

`--key` is case-insensitive and must identify exactly one eligible entry. It
selects this invocation’s work, while the report keeps the entire audit scope.
`--refresh` clears only the selected decisions and bypasses cached response reads.
`--encoding` (default UTF-8) and `--include-source` apply to BibTeX/AUX input.
`--verbose` shows redacted response diagnostics on stderr.

The default output is `<input-stem>.bib-lint/` beside the input. `--output` names a
**directory**, with relative paths resolved from the caller’s directory:

```text
references.bib-lint/
  report.json             completed report
  report.tmp.json         active checkpoint (takes precedence in the UI)
  report.json.lock        stable advisory lock
  cache/
    checksum.json
    checksum.json.lock
    <citation-key>/<source>_<timestamp>.<extension>
  report.agent.json       optional externally supplied manual review
```

Each completed source is saved atomically. Rerun the same command to resume:
saved non-error outcomes are reused, errors and unfinished sources are retried.
Stop with Ctrl-C; the checkpoint remains. The prior final report stays intact
until every eligible entry completes its source lookups. A one-key audit can
finish successfully while other entries remain Pending. Concurrent writers fail
clearly. Different parsed entries, usage, or eligibility require a **new output
directory**, including when using `--refresh`. Comment-only edits do not invalidate
parsed input. Policy/registry changes recompute decisions for the same input.
Unrelated workspace files and manual reviews are preserved.

Progress, warnings, retry messages, and verbose diagnostics go to **stderr**.
Stdout contains the final human summary or exactly one object with `--json`:

```json
{
  "schema_version": 1,
  "command": "verify",
  "status": "partial",
  "complete": false,
  "output_dir": "/papers/audit",
  "report_path": null,
  "checkpoint_path": "/papers/audit/report.tmp.json",
  "scope": "all",
  "summary": {
    "total": 2, "eligible": 2, "completed": 1, "pending": 1,
    "used": null, "unused": null, "correct": 1, "invalid": 0,
    "unresolved": 0, "partial_match": 0, "needs_review": 0, "source_failures": 0
  },
  "warnings": [],
  "error": null
}
```

Statuses are `completed`, `partial`, `interrupted`, and `failed`. Counts describe
the whole workspace. Paths are absolute or null when absent; unavailable scope
and summary are null. Errors have `code` and `message`. Exit **0** means requested
work finished, even with invalid references or source failures; **2** indicates
argument/input/lock/storage/launch failure; **130** indicates interruption.
Help and version exit 0. No findings-based CI exit policy is applied.

### Migration and report schema

The former CLI `parse` command is retired. Replace `parse ... -o FILE` followed by
`verify FILE` with `verify INPUT.bib --output DIRECTORY`. The Python parsing API
remains available for parsing-only consumers. CLI cache relocation was removed:
evidence belongs to the selected audit folder. Legacy report viewing still allows
cache selection in the sidebar.

New managed reports use **schema 3**, retaining entries and the existing source
and correctness vocabulary, with explicit scope:

```json
{
  "schema_version": 3,
  "verification_scope": {"mode": "all", "eligible_keys": ["example"]},
  "summary": {"total_count": 1, "total_not_used": null},
  "items": [{"entry": {"key": "example", "type": "book", "fields": {"title": "Example"}, "persons": {}}, "validations": {}}]
}
```

With AUX, mode is `used`, eligible keys preserve original spelling/order, and
`validations.is_used` is boolean. Without AUX it is absent. Verification adds
`validations.correctness`: `is_correct` is the sole true/false/null verdict;
`methods` contains source outcomes, comparisons, evidence and timestamps;
`consensus`, `reason`, `canonical_ref`, `policy_version`, and `complete` retain
their existing meanings. Partial source checkpoints leave `is_correct` null.
Run metadata includes a versioned parsed-input/scope fingerprint, registry,
comparison policy (currently 5), orchestration version, and completion state.

The viewer reads legacy schema-2 reports, including unknown usage. `verify
legacy.json --output imported-audit` imports schema 2 only when every entry has
boolean usage, normalizing to used-only scope and reusing compatible outcomes.
Unknown-scope v2 input must be audited from its bibliography directly. Imported
JSON, external caches, and schema-1 agent sidecars are never rewritten or copied
implicitly. Previous releases do not understand schema 3; retain historical v2
artifacts if using an older tool.

## Local UI workflow

`bib-lint view` opens local workflow controls even without a report. Open
http://127.0.0.1:8501; `--port` selects another port. Enter local bibliography,
optional AUX, and output-directory paths. **Parse** creates a network-free preview;
**Verify** performs the full workflow directly. **Open audit directory** selects
existing work. The sidebar still opens legacy report/cache/agent paths.

**Verify selected key**, **Refresh**, and **Refresh selected key** use the CLI’s
eligibility rules. A managed subprocess performs lookups while the page displays
saved progress and a bounded diagnostic tail. Reloading/navigation reattaches to
the job instead of starting another. One session can have one active job; a
workspace can have only one active writer. Controls stay disabled while running.
**Stop** sends SIGINT once; the job stays Stopping until it exits. **Resume** then
reuses completed outcomes without repeating a refresh. Closing a browser page
does not cancel the job; stopping the server interrupts and reaps managed children.

The overview includes all references and keeps **Used** separate from audit
**Progress**. Usage is Unknown without AUX; progress counts completed eligible
entries. Provider errors are source findings, distinct from invalid references
and process failures. Click a reference cell to inspect Comparison, Cached
responses, and Raw log. Cached HTML is displayed as source, never executed.
Agent evidence is shown separately and never affects automated metrics.

## Verification methods and policy

Verification runs six independent sources: **arXiv, PMLR, JMLR, ACL Anthology,
NeurIPS and OpenReview**. Crossref, OpenAlex and Semantic Scholar live adapters
have been removed. Historical reports and raw cached evidence remain readable.

Each provider owns its supported URLs/identifiers, source routing, direct lookup,
bounded discovery and normalization. Missing URLs do not prevent title or
identifier discovery through official APIs/catalogs. Publication archives use
venue/year or volume context; missing context and exhausted budgets remain
explicit incomplete-search diagnostics. Scoped misses never prove global absence.
See [source strategies and limits](docs/sources.md).

Providers implement a typed retrieval protocol and register explicitly in Python.
The shared executor selects identity, compares metadata and makes decisions;
providers never supply correctness or votes. The same core and UI support
extensions. See [the provider contract and test harness](docs/providers.md).

Identifiers cannot establish identity for unrelated titles. Title, ordered authors,
year, venue and supplied identifiers are compared conservatively. Compatible
initials, abbreviated venues and missing fields remain uncertain. An absent input
venue is not checked. Checks cover core citation metadata, not claim support,
pages, volume, edition or citation style.

arXiv is authoritative for its preprint records; publication archives for their
published records. OpenReview qualifies explicit accepted/publication evidence
for configured ICLR, ICML, NeurIPS and TMLR main venue series. Public submissions,
rejected/withdrawn records or unknown acceptance cannot confirm conference
publication. Anonymous authors and missing publication dates remain unknown.

Conflicting primary records, ambiguous searches and preprint/publication version
differences require review. Duplicate hosting is corroboration rather than a
majority vote. `false` requires a confirmed discrepancy; `true` requires checked
fields to match; insufficient evidence produces `null`. Provider failures remain
separate from metadata findings and do not suppress other sources.

New audits record ordered provider descriptors, revisions and policies alongside
protocol version 1, orchestration version 2 and comparison policy 5. Changes to
these values invalidate saved decisions, while fresh checksum-valid raw responses
can be reused. The previous final remains until complete replacement; manual
reviews keep their independent entry bindings. No credentials are required or
requested. Public access failures remain source diagnostics.

Responses are stored under the audit directory’s `cache/`:

```text
cache/
  checksum.json
  checksum.json.lock
  lambert2024tulu/
    arxiv_1780000000000000000.xml
    openreview_1780000000000000001.json
    pmlr_1780000000000000002.html
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

Requests use descriptor-defined 20-second timeouts and pacing (3.1 seconds for
arXiv, 1 second otherwise). Transient failures retry after 2 then 4 seconds;
numeric `Retry-After` is honored up to 10 seconds. Longer or nonfinite delays stop
retries and report unavailability. Jitter and HTTP-date Retry-After are not
implemented. Fetch, HTTP-attempt, catalog-page, candidate and redirect budgets
also apply, including to discovery. See [provider policy defaults](docs/providers.md).
Backoff messages appear as they happen.

### Separate agent web reviews

The viewer automatically reads `references.agent.json` next to `references.json`
(or `references.tmp.json`). The sidebar's **Agent evidence** path can select a
different sidecar. Missing evidence is optional; malformed evidence shows a warning
while the automated report remains usable.

An agent review is a separate, manually researched assessment, not another independent
API vote. The overview adds **Agent** and **Agent note** columns. Automated status,
metrics, found counts and consensus stay unchanged. Agent findings also appear in
Diff, suggested corrections, Resolved Sources, Raw log, and an **Agent evidence** tab
with primary links, reasoning, checked fields and limitations. “Show errors only”
includes errors identified by either assessment.

Sidecar schema 1 has `source: "agent"`, provenance timestamps, the original report
SHA-256, a scope/summary, and `items`. Each review contains `citation_key`,
`entry_sha256`, `reviewed_at`, a single `status`, `summary`, `checked_fields`,
`evidence` (URL and what it supports), and optional field `comparisons` using the
existing match/mismatch/partial_match/unknown vocabulary. It never contains a
duplicate `is_correct` verdict. `entry_sha256` uses `viewer.agent.entry_digest`:
SHA-256 of UTF-8 JSON with sorted keys, no ASCII escaping, and compact separators.

Reviews are bound to the exact parsed entry, not its citation key alone. Changed
entries are flagged as stale and their agent verdicts/corrections are withheld.
A new API run can still use the review when its parsed bibliography entry is unchanged.
The original report hash is provenance, not a requirement to reproduce the same API
results. All loading is read-only; the CLI verifier does not read or modify this file.

The supplied sidecar reviews all 52 used citations by web search. “Correct” is limited
to the listed bibliographic fields; it does not certify scientific claims or every
ancillary BibTeX field. Version conflicts, unavailable publisher evidence, and
software release dates remain explicit review items.

### Status vocabulary

All UI status columns use the heading **Status**, and lookup providers are called
**Sources**. Native Streamlit badges and read-only MultiselectColumn chips share
one color palette (no custom HTML, CSS, or JS).

| Check | Display statuses | Meaning |
| --- | --- | --- |
| Reference | Correct (green), Invalid (red), Unresolved (red), Partial match (orange), Needs review (orange) | Completed decision about citation metadata |
| Reference progress | Pending (orange), Skipped (gray) | Incomplete check or unknown usage; Skipped is reserved for explicitly unused citations |
| Source lookup | Found (green), Not found (orange), Ambiguous (orange), Failed (red), Not applicable (gray) | Record identified, no match, multiple matches, request failure, or source not applicable |
| Field comparison | Match (green), Mismatch (red), Insufficient data (orange), Partial match (orange), Not checked (gray) | Equal, confirmed difference, insufficient evidence, or field not checked |

Finding a record does not mean the citation is correct. A failed request does not
mean the citation is invalid. These distinct meanings are retained rather than
collapsing every check into success/failure. HTTP codes remain visible in cached
responses (2xx green, errors red).

Both schema 2 and schema 3 retain the decision vocabulary: `is_correct` remains the sole stored overall
verdict, with `complete` and `is_used` determining Pending/Skipped. Source results
remain in `correctness.methods` with their original `status` tokens (`found`,
`not_found`, `ambiguous`, `error`, `not_applicable`). Field comparisons retain
`result` (`match`, `mismatch`, `unknown`, `not_checked`). Cache manifests retain
`method`; summary keys retain `incorrect` and `method_errors`. These are historical
storage/API names, not UI labels. Imported source reports, raw payloads, checksums, and agent evidence are not rewritten. CLI labels use the shared status vocabulary
and call summary counts “invalid” and “source failures”.

### Partial matches and unresolved references (comparison policy 5)

Unresolved now means no reference record is available to compare. A terminal
BibTeX `others` marker yields Partial match when the supplied authors exactly
match the source's ordered prefix and the source lists more authors. Confirmed
prefix differences remain Mismatch; ambiguous initials remain Insufficient data.
Partial match is amber and does not assert that omitted authors were verified.
References with available records but conflicting or incomplete evidence show
Needs review. All completed verdicts count toward progress, with separate summary
counts for Partial match and Needs review. `is_correct` remains null for these
cases; no duplicate overall verdict is stored.

## Python API and development checks

```python
from bib_lint import parse_bib, parse_file, parse_string
from bib_lint.audit import run_audit

# Existing parsing-only API still writes schema 2.
bib_result, aux_result = parse_bib("references.bib", "paper.aux")
# New managed workflow writes schema 3.
workspace, report, warnings = run_audit("references.bib", output="audit")
```

`parser.py`/`models.py` preserve TeX spelling, entry order, structured names,
macros, custom fields, preambles and original source bytes/hash. BibTeX `crossref`
inheritance is not applied. `aux.py` extracts citations; `scope.py` records
eligibility; `audit.py` owns workspace orchestration; `storage.py` provides
atomic writes/locks. Verification adapters, matching, consensus, HTTP and cache
remain separated under `verification/`. `viewer/jobs.py` owns subprocesses;
`viewer/app.py` renders native Streamlit components.

```sh
uv sync
uv run pytest -m unit
uv run pytest -m workflow
uv run pytest -m ui
uv run pytest -m package
uv run coverage run -m pytest -m 'not package'
uv run coverage report
uv run ruff check .
uv run ruff format --check .
uv build
```

Shared records and provider doubles live in `tests/support.py`. Tests block
external socket connections, use HTTP mock transports, controlled pacing/retry
clocks, temporary files, storage fault injection and process doubles. The package
check builds/installs a wheel in temporary `UV_TOOL_DIR`/`UV_TOOL_BIN_DIR`, invokes
it outside the checkout, performs a zero-eligible audit, and checks localhost
viewer readiness. It needs uv’s dependency/build cache or package downloads;
it never replaces the user’s tool installation or queries scholarly providers.

Branch coverage reports runtime modules only; generated files and dependencies
are excluded. Coverage is measured without a numeric acceptance threshold.

## Local development setup

Install uv, then run the Python task runner from the checkout:

```sh
uv run invoke init
```

The task in `tasks.py` syncs development dependencies and initializes OpenSpec
with Codex skills using the pinned CLI version 1.14.1 through `npx`. Node.js
20.19+ and npm are required for that step; no global OpenSpec installation is
needed. Invoke is a development dependency, excluded from the installed tool.

For Python development without OpenSpec:

```sh
uv run invoke init --no-openspec
uv run invoke --list
```

OpenSpec plans/configuration in `openspec/`, generated skills in
`.agents/skills/openspec-*/`, and `.agents/skills/.openspec-target` stay local and
gitignored. Rerunning initialization refreshes the generated skills while retaining
existing planning files and configuration.
