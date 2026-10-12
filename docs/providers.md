# Adding a provider

Providers retrieve evidence; shared code selects identity, compares fields and makes decisions. Implement `Provider` from `bib_lint.verification.providers.protocol`, supplying a versioned `ProviderDescriptor`, `applicability(query)` and `lookup(query, context)`.

The descriptor declares a stable lowercase ID, display name, adapter revision, evidence category, canonical priority, exact hosts and finite request/discovery policy. Register trusted instances explicitly in the built-in registry or pass a collection to the Python workflow's `methods` argument. The former callable mapping of verdict-returning functions is replaced by provider instances; there is no package auto-discovery or CLI provider-selection option.

Use immutable `LookupQuery`, `Candidate`, `LookupAttempt` and `LookupResult` values. Preserve unknown fields and ordered authors. Give candidates canonical HTTPS URLs and source/field provenance. Candidates carry record kind, publication status and source version, never `is_correct`, field differences or votes. Avoid filling source metadata from query hints.

All HTTP must go through `context.get`/`context.json`; mark catalog/search requests with `page=True` and register shortlisted candidates with `context.shortlist`. Default limits are 20 seconds per request, 10 fetches, 30 HTTP attempts (retries/redirects included), 5 catalog pages, 100 candidates and 4 redirects per fetch. Default pacing is 1 second with retry delays 2/4 seconds and Retry-After capped at 10 seconds; arXiv uses 3.1-second pacing. Cache hits still consume fetch/page budgets, but no network-attempt budget. Checksums, raw bodies and credential redaction are shared.

Record every direct/discovery strategy and searched scope. Complete scoped misses mean no record found in that scope. Missing routing context or budget exhaustion is incomplete evidence, never proof of nonexistence. Source failures stay distinct from citation discrepancies. Interruptions and storage errors must propagate.

`tests/provider_support.py` contains an executable `FixtureProvider` example with a deliberately different payload shape and the reusable `assert_contract(provider, query, context)` harness. `tests/test_provider_protocol.py::test_reusable_conformance_with_different_payload` runs that example. Supply offline successful, empty and malformed payload fixtures plus direct/discovery, boundary, budget and uncertainty cases; run the shared harness against each fixture. Tests use a fake transport/clock and forbid scholarly network access.

Bump `adapter_version` whenever retrieval or normalization changes, and version discovery configuration when changing hosts, venue qualification or budgets. The entire descriptor participates in resume compatibility. Changed descriptors invalidate saved decisions; checksum-valid raw responses can still be reused. Trusted extensions are ordinary Python code, not sandboxed plugins.

For example, extend the default registry through the workflow API:

```python
from bib_lint.audit import run_audit
from bib_lint.verification.providers import METHODS

providers = [*METHODS.values(), MyProvider()]
workspace, report, warnings = run_audit("references.bib", output="audit", methods=providers)
```

`MyProvider` is your protocol implementation. Supplying `methods` replaces the
registry, so include the built-ins explicitly when extending them. The fixture
extension workflow and UI tests exercise this mechanism without source-specific
executor or presentation changes.
