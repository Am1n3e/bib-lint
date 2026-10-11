# Official benchmark harnesses

Run published inputs through bib-lint's normal audit API, using the current arXiv,
PMLR, JMLR, ACL Anthology, NeurIPS and OpenReview providers. Original labels,
splits, duplicate citations and case counts are preserved. Failed cases are never
removed or relabeled.

| Harness | Pinned inputs | Evaluation |
| --- | --- | --- |
| `hallmark` | v1.2.3, commit `f774fa40675daa83eca6201637a94c4536b7bb3e`; 1,119 dev, 831 test, 121 stress cases | Unmodified official Python evaluator, both modes |
| `zenodo` | v1.1.0, record 23236264; 104 cases, 69 verified and 35 problematic | Published binary protocol; no scorer released |
| `gptzero` | Original public NeurIPS 2025 sheet; 100 reported issues at acquisition | Detection summary; no official scorer or negative examples |
| `hallucitation` | HalluCitation Matters, arXiv 2601.18724v1, Appendix B; 296 references in 295 numbered rows | Published positive examples; no official scorer or negative examples |

Upstream sources: [HALLMARK](https://github.com/rpatrik96/hallmark),
[Zenodo v1.1.0](https://zenodo.org/records/23236264),
[GPTZero article](https://gptzero.me/news/neurips/) and its linked
[original sheet](https://docs.google.com/spreadsheets/d/14hIuCK7HCnGhdCuxfwp1wIYbbHMn-K3FNvY9NgWGW0Y/edit),
[HalluCitation Matters](https://arxiv.org/abs/2601.18724v1).

## Commands

Run from this checkout. The optional dependency group installs HALLMARK's official
evaluator at the dataset's immutable commit. It adds no runtime dependencies to
the installed bib-lint tool.

```sh
uv sync --group benchmark
uv run --group benchmark python -m evaluation.harness list
uv run --group benchmark python -m evaluation.harness prepare
uv run --group benchmark python -m evaluation.harness run --benchmark hallmark
uv run --group benchmark python -m evaluation.harness run --benchmark zenodo
uv run --group benchmark python -m evaluation.harness run --benchmark gptzero
uv run --group benchmark python -m evaluation.harness score --benchmark hallmark
uv run --group benchmark python -m scripts.check_baseline
```

Omit `--benchmark` or use `--benchmark all` to process all registered sources.
All four collections are available. Exit 2 records failed acquisition or harness
errors; genuine bib-lint failures remain in the baseline. Exit 0 means requested
harness work finished; it does not assert accuracy or full coverage. Progress goes to
stderr, final JSON to stdout and `<root>/<command>-summary.json`.

```sh
# Partial smoke run, or a single official split:
uv run --group benchmark python -m evaluation.harness run --benchmark zenodo --limit 2
uv run --group benchmark python -m evaluation.harness run --benchmark hallmark --split test_public
```

`--limit` is explicitly partial. Rerun without it to continue the full split.
Rerun the same command to resume. Add `--retry-errors` to revisit execution failures
and cases containing source errors; bib-lint reuses completed provider outcomes.
Ctrl-C preserves completed cases and the current provider checkpoint. Provider
timeouts, retries and host pacing apply, so full runs can take substantial time.
`--verbose` prints provider progress; each case also retains a `progress.log`.
The default is eight concurrent cases. Use `--workers N` to choose another value.
Every worker has an independent client, evidence and cache. A shared transport
coordinates host pacing across workers, including retries, while keeping bib-lint's
normal provider request policies. The worker count is recorded with the run and
must match on resume. Work submission is bounded so interruption does not leave
the rest of the corpus queued.

`--root /absolute/path` selects another output folder. Sources are frozen on
first acquisition and SHA-256 checked on every load. The mutable GPTZero sheet
is never silently refreshed. Changed tool code, provider registry, conversion,
prediction mapping or dataset hashes require a fresh root for another run.
A stable root lock rejects concurrent harness writers.

## Outputs

Default root: `evaluation/.artifacts/` (gitignored).

```text
.artifacts/
  sources/<benchmark>/
    snapshot.json              releases, URLs, acquisition time, SHA-256 hashes
    <original files>            original download bytes and labels
  runs/<benchmark>/<split>/
    run-config.json             tool/harness source hashes and provider registry
    run-status.json             counts and completion status
    progress.json               incrementally updated completed-case counts
    predictions.jsonl           atomic bib-lint prediction checkpoint
    evaluation.json             metrics, evaluation type, coverage and caveats
    official_predictions.jsonl  HALLMARK Prediction-format export
    official_format_results.csv Zenodo original columns plus bib_lint result
    cases/<hashed-case-id>/
      input.json                label-free bib-lint input
      conversion.json           raw text, extracted fields, conversion version
      progress.log
      input-error.json          present on conversion/execution failure
      tool-error.json           genuine bib-lint exception, kept in the baseline
      audit/
        report.json             normal report, usable with bib-lint view
        report.tmp.json         active/interrupted audit checkpoint
        cache/                 raw provider responses and checksums
```

Directory names are digests of case IDs. Predictions retain source errors,
uncertainty, elapsed time and request counts. Labels are used only for scoring;
they are never passed into provider lookups.

## Evaluation conditions

**HALLMARK:** original structured fields go directly into bib-lint JSON input,
including malformed TeX. Canary exclusion follows the official loader: the stress
file has 122 rows including one canary. `Correct` maps to `VALID`, `Invalid` to
`HALLUCINATED`, and review/unresolved states to `UNCERTAIN`. Execution failures
have `evaluated=false`. The pinned evaluator excludes uncertainty from
conservative classification; aggressive mode treats uncertainty and missing
answers as hallucinations. Inspect coverage alongside scores. Supplementary
conservative accuracy is explicitly separate from official metrics. Confidence
0.5 is an export placeholder; calibration metrics are not meaningful for this
tool. Full upstream evaluator output is retained. The tool does not emit HALLMARK
field subtest predictions, so those metrics remain unavailable.

**Zenodo:** `Correct` maps to `not_flagged`; mismatch, unresolved and review-required
outcomes map to `flagged`, following the published interpretation protocol. Input
failures and provider failures without usable evidence are `not_evaluated`.
Accuracy, precision, recall, false-positive rate and F1 use the full denominator
and are withheld until every case is evaluated. Coverage is always reported.

**GPTZero:** the original sheet retains comments and paper links. The detection
summary reports the fraction of all reported issues flagged, including failed and
missing cases in the denominator. It cannot measure accuracy, precision or
false-positive rate. These reported positives are not independently adjudicated
by the harness. Some references overlap other benchmarks; scores remain separate
and are not pooled as independent samples.

**HalluCitation Matters:** the frozen HTML paper's Appendix B publishes 295
numbered rows with explicit HalluCitation examples. Row 226 contains two separate
references; both are run, giving 296 reference cases. The original cell is retained
alongside the split examples. No example is dropped or corrected. Results use the
same positive-collection detection summary as GPTZero; no official scorer, negative
reference labels or full-audit recall denominator is published. This is evaluation
on the paper's published examples, not replication of its entire 17,000-paper audit.

**Raw citation preprocessing:** Zenodo, GPTZero and HalluCitation provide strings; bib-lint needs
structured entries. A limited deterministic adapter extracts common APA, IEEE,
quoted, ACL and export-style formats without consulting sources or labels. Original
text, encoding artifacts and extracted fields remain reviewable. Unsupported
formats stay as failed cases. This is harness preprocessing, not an official
parser. Inspect `conversion.json` for the raw-string datasets before drawing
conclusions. These releases do not provide an official reference-to-BibTeX adapter.
The current full input validation covers all 2,571 cases, with no conversion or
schema errors; `input-validation.json` records that evidence. Per-run evaluation
separately records failure stages and `harness_ok`, so an input/export/setup
failure cannot silently be treated as a genuine tool failure.

The provider restriction to arXiv and ML publishers applies even to references
outside that scope. Evaluations therefore measure the configured tool's actual
coverage. Online availability can change; saved responses and error counts
document each run.

## Validation

```sh
uv run --group benchmark pytest -q tests/test_benchmarks.py
uv run --group benchmark pytest -q
uv run --group benchmark ruff check src tests evaluation
```

Tests use mocked HTTP and local fixtures. They check original field preservation,
canaries, citation formats, prediction mapping, missing-case denominators, exact
upstream evaluator outputs, interruption checkpoints, resume/retry behavior,
snapshot integrity, complete appendix extraction, isolated concurrent clients,
shared host pacing and tool-failure handling.

`scripts.check_baseline` performs the final completion audit without contacting
providers or changing the running harness. It checks every expected case against
the original sources, compares predictions with native reports, verifies evidence
bytes, and reruns the available scoring logic independently. It writes
`baseline-verification.json` and exits 2 while cases are pending or a check fails;
exit 0 requires all four collections to pass. Genuine recorded bib-lint exceptions
are allowed, but input, setup, storage and export failures are not.
After the full audit succeeds, it also writes `baseline-results.json` with all
verified scores and `baseline-results.csv` with separate rows for every benchmark,
split and HALLMARK uncertainty mode. Undefined metrics remain empty; positive-only
collections are never assigned accuracy or precision. No scores are pooled across
overlapping datasets. These final exports are withheld until the full run passes.
The official evaluator emits `NaN` for unsupported type metrics. Final JSON
encodes non-finite values as `null`, and final CSV leaves them empty; the original
per-split evaluator output is retained unchanged.
