"""Verify every entry using independently executed provider adapters."""

import copy
import hashlib
import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from bib_lint.scope import eligible_items, fingerprint, selected_items, validate_report
from bib_lint.status import reference_status, source_status
from bib_lint.storage import report_lock, report_paths
from bib_lint.storage import write_json as _write_json
from bib_lint.verification.consensus import build_consensus
from bib_lint.verification.http import LookupFailure, MetadataClient
from bib_lint.verification.matching import input_record
from bib_lint.verification.providers import METHODS


def verify_reference(
    entry: dict,
    client: MetadataClient,
    *,
    methods=None,
    previous=None,
    progress=None,
    checkpoint=None,
) -> dict:
    record = input_record(entry)
    record["input_url"] = entry.get("fields", {}).get("url", "")
    results = []
    saved = {m["name"]: m for m in (previous or [])}
    for name, function in (METHODS if methods is None else methods).items():
        if name in saved and saved[name]["status"] != "error":
            results.append(saved[name])
            if progress:
                progress(f"  {name}: Resumed ({source_status(saved[name]['status'])})")
            continue
        if progress:
            progress(f"  {name}: Fetching ...")
        client.progress = (
            (lambda message, name=name: progress(f"  {name}: {message}")) if progress else None
        )
        client.citation_key = entry.get("key", "_unknown")
        client.method = name
        start = len(client.evidence)
        try:
            if not record["title"]:
                raise LookupFailure(
                    "insufficient_input", "Entry has no title for identity checking"
                )
            result = function(record, client)
        except OSError:
            # Evidence persistence failures are execution errors, not provider findings.
            raise
        except Exception as exc:
            # One provider failing must not prevent other independent lookups.
            code = exc.code if isinstance(exc, LookupFailure) else "invalid_response"
            result = {
                "name": name,
                "status": "not_found" if code == "not_found" else "error",
                "found_ref": None,
                "agrees_with_consensus": None,
                "differences": [],
            }
            if code != "not_found":
                result["error"] = {
                    "code": code,
                    "message": str(exc) if isinstance(exc, LookupFailure) else type(exc).__name__,
                }
        result["requests"] = client.evidence[start:]
        result["checked_at"] = datetime.now(UTC).isoformat()
        results.append(result)
        if checkpoint:
            checkpoint(copy.deepcopy(results))
        if progress:
            error = result.get("error", {})
            label = source_status(result["status"])
            if result["status"] == "error":
                label += f": {error.get('code', 'unknown')}"
            if result["status"] == "error" and error.get("message"):
                label += f" — {error['message']}"
            progress(f"  {name}: {label}")
    client.progress = None
    return build_consensus(results)


_validate_report = validate_report


def _fingerprint(report):
    inputs = [
        {"entry": i["entry"], "is_used": i["validations"].get("is_used")} for i in report["items"]
    ]
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def _totals(report):
    totals = {
        "correct": 0,
        "incorrect": 0,
        "unresolved": 0,
        "partial_match": 0,
        "needs_review": 0,
        "method_errors": 0,
        "skipped_unused": 0,
    }
    for item in report["items"]:
        if report.get("verification_scope", {}).get("mode") != "all" and not item[
            "validations"
        ].get("is_used"):
            totals["skipped_unused"] += 1
            continue
        result = item["validations"].get("correctness")
        if result is None or result.get("complete") is False:
            continue
        status = reference_status(item["validations"])
        key = "incorrect" if status == "Invalid" else status.lower().replace(" ", "_")
        totals[key] += 1
        totals["method_errors"] += sum(m["status"] == "error" for m in result["methods"])
    return totals


def verify_file(
    path: str | Path,
    *,
    output: str | Path | None = None,
    cache_dir: str | Path = ".bib-lint-cache",
    refresh=False,
    verbose=False,
    citation_key: str | None = None,
    progress: Callable[[str], None] | None = None,
    client=None,
    methods=None,
) -> tuple[Path, dict]:
    source = Path(path)
    destination, checkpoint = report_paths(Path(output) if output is not None else source)
    registry = METHODS if methods is None else methods
    with report_lock(destination):
        # A finished run has renamed the temporary file; accept the original command again.
        readable = source
        if not source.exists() and source.resolve() in {
            destination.resolve(),
            checkpoint.resolve(),
        }:
            readable = checkpoint if checkpoint.exists() else destination
        report = json.loads(readable.read_text(encoding="utf-8"))
        _validate_report(report)
        if checkpoint.exists() and checkpoint.resolve() != readable.resolve():
            saved = json.loads(checkpoint.read_text(encoding="utf-8"))
            _validate_report(saved)
            if _fingerprint(saved) != _fingerprint(report):
                raise ValueError(f"Checkpoint belongs to different inputs: {checkpoint}")
            report = saved
        return verify_report_locked(
            report,
            destination,
            checkpoint,
            cache_dir=cache_dir,
            refresh=refresh,
            verbose=verbose,
            citation_key=citation_key,
            progress=progress,
            client=client,
            methods=registry,
        )


def verify_report_locked(
    report,
    destination,
    checkpoint,
    *,
    cache_dir,
    refresh=False,
    verbose=False,
    citation_key=None,
    progress=None,
    client=None,
    methods=None,
):
    """Execute under the caller's report lock; never reacquire it."""
    registry = METHODS if methods is None else methods
    selected = selected_items(report, citation_key)
    used = eligible_items(report)
    input_hash = _fingerprint(report) if report["schema_version"] == 2 else fingerprint(report)
    run = report.get("verification_run")
    expected = {"fingerprint": input_hash, "methods": list(registry), "policy_version": 4}
    if report["schema_version"] == 3:
        expected["orchestration_version"] = 1
    reusable = run and all(run.get(key) == value for key, value in expected.items())
    if not reusable or refresh:
        for item in report["items"] if not reusable else selected:
            item["validations"].pop("correctness", None)
    report["verification_run"] = {**expected, "complete": False}
    _write_json(checkpoint, report)
    owned = client is None
    client = client or MetadataClient(Path(cache_dir), refresh=refresh, verbose=verbose)
    if verbose:
        client.verbose = True
    try:
        for index, item in enumerate(selected, 1):
            if progress:
                progress(f"Verifying {index}/{len(selected)}: {item['entry'].get('key', '?')}")
            previous = item["validations"].get("correctness", {}).get("methods", [])

            def save_method(results, item=item, previous=previous):
                merged = {m["name"]: m for m in previous}
                merged.update({m["name"]: m for m in results})
                results = [merged[name] for name in registry if name in merged]
                result = build_consensus(results)
                result["complete"] = len(results) == len(registry)
                if not result["complete"]:
                    result["is_correct"] = None
                item["validations"]["correctness"] = result
                report.setdefault("summary", {})["verification"] = _totals(report)
                _write_json(checkpoint, report)

            result = verify_reference(
                item["entry"],
                client,
                methods=registry,
                previous=previous,
                progress=progress,
                checkpoint=save_method,
            )
            result["complete"] = True
            item["validations"]["correctness"] = result
            report.setdefault("summary", {})["verification"] = _totals(report)
            _write_json(checkpoint, report)
            if progress:
                state = reference_status(item["validations"]).lower()
                consensus = result["consensus"]
                progress(f"  status: {state}")
                progress(f"  found: {consensus['records_found']}/{consensus['applicable']}")
                progress(f"  consensus: {consensus['display']}")
    finally:
        if owned:
            client.close()
    totals = _totals(report)
    report.setdefault("summary", {})["verification"] = totals
    complete = all(
        item["validations"].get("correctness", {}).get("complete", False) for item in used
    )
    report["verification_run"]["complete"] = complete
    _write_json(checkpoint, report)
    if complete:
        checkpoint.replace(destination)
    elif progress:
        progress("Other eligible references remain pending; checkpoint retained.")
    return destination if complete else checkpoint, totals
