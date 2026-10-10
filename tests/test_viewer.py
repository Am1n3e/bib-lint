import copy
import hashlib
import json

import pytest
from defusedxml.common import EntitiesForbidden
from streamlit.testing.v1 import AppTest
from support import viewer_main

from bib_lint.viewer.data import comparison_rows, pretty_xml, read_response, suggestions, table_rows


def fixture_report():
    entry = {
        "key": "sample",
        "type": "article",
        "fields": {"title": "Example", "year": "2024"},
        "persons": {},
    }
    method = {
        "name": "crossref",
        "status": "found",
        "authority": True,
        "agrees_with_consensus": True,
        "found_ref": {
            "url": "https://doi.org/10.1234/example",
            "identifiers": {"doi": "10.1234/example"},
        },
        "comparisons": [{"field": "year", "input": "2024", "found": 2025, "result": "mismatch"}],
        "differences": [{"field": "year", "input": "2024", "found": 2025, "result": "mismatch"}],
    }
    result = {"is_correct": False, "complete": True, "reason": "Year differs", "methods": [method]}
    item = {"entry": entry, "validations": {"is_used": True, "correctness": result}}
    unused = {"entry": {**entry, "key": "unused"}, "validations": {"is_used": False}}
    return {"schema_version": 2, "items": [item, unused]}


def test_all_rows_counts_and_status():
    rows = table_rows(fixture_report())
    assert len(rows) == 2
    assert list(rows[0]) == [
        "Citation key",
        "Used in paper",
        "Status",
        "Found",
        "Consensus",
        "Note",
    ]
    assert rows[0]["Found"] == rows[0]["Consensus"] == "1/1"
    assert rows[1]["Used in paper"] == "No"
    assert rows[1]["Status"] == "Skipped"


def test_comparisons_and_evidence_based_proposals():
    item = fixture_report()["items"][0]
    row = comparison_rows(item)[0]
    assert list(row) == ["Source", "Field", "Status", "Your value", "Source's value"]
    assert row["Source's value"] == "2025"
    assert suggestions(item)[0]["Suggested"] == "2025"
    uncertain = copy.deepcopy(item)
    uncertain["validations"]["correctness"]["is_correct"] = None
    assert suggestions(uncertain) == []


def test_cache_read_checks_integrity_without_modifying_files(tmp_path):
    raw = b"<html>Original\ncontent</html>"
    path = tmp_path / "sample" / "publisher_1.html"
    path.parent.mkdir()
    path.write_bytes(raw)
    entry = {"path": "sample/publisher_1.html", "sha256": hashlib.sha256(raw).hexdigest()}
    assert read_response(tmp_path, entry)[0] == raw
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="Checksum"):
        read_response(tmp_path, entry)
    assert path.read_bytes() == b"changed"
    with pytest.raises(ValueError, match="Invalid cache path"):
        read_response(tmp_path, {**entry, "path": "../outside"})


def test_xml_pretty_print_disallows_entities():
    assert "\n  <title>" in pretty_xml("<feed><title>Example</title></feed>")
    with pytest.raises(EntitiesForbidden):
        pretty_xml('<!DOCTYPE x [<!ENTITY s "secret">]><x>&s;</x>')


def test_streamlit_overview_detail_and_back(tmp_path, monkeypatch):
    report = tmp_path / "references.json"
    report.write_text(json.dumps(fixture_report()))
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_function(viewer_main, default_timeout=30).run()
    assert not app.exception
    assert len(app.dataframe[0].value) == 2
    assert all(metric.help for metric in app.metric)
    metrics = {metric.label: metric.value for metric in app.metric}
    assert list(metrics) == [
        "Total",
        "Used",
        "Progress",
        "Skipped",
        "Correct",
        "Invalid",
        "Unresolved",
        "Partial match",
        "Needs review",
    ]
    assert metrics == {
        "Total": "2",
        "Used": "1/2",
        "Progress": "1/1",
        "Skipped": "1/2",
        "Correct": "0/1",
        "Invalid": "1/1",
        "Unresolved": "0/1",
        "Partial match": "0/1",
        "Needs review": "0/1",
    }
    app.query_params["key"] = "sample"
    app.run()
    assert not app.exception
    assert app.header[0].value == "sample"
    assert all(metric.help for metric in app.metric)
    assert [tab.label for tab in app.tabs] == ["Comparison", "Cached responses", "Raw log"]
    next(button for button in app.button if button.label == "← All references").click().run()
    assert not app.exception
    assert app.title[0].value == "Bib-Lint"


def test_overview_filters_keep_global_metrics(tmp_path, monkeypatch):
    report = fixture_report()
    # Put unused first to exercise filtering independently of source row order.
    report["items"].reverse()
    (tmp_path / "references.json").write_text(json.dumps(report))
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_function(viewer_main).run()
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert list(app.dataframe[0].value["Citation key"]) == ["sample"]
    assert app.metric[0].value == "2"
    app.toggle[0].set_value(False)
    app.toggle[1].set_value(True).run()
    assert list(app.dataframe[0].value["Citation key"]) == ["sample"]
    report["items"][1]["validations"]["correctness"]["is_correct"] = True
    (tmp_path / "references.json").write_text(json.dumps(report))
    app.run()
    assert not app.exception
    assert not app.dataframe
    assert app.info[0].value == "No references match these filters."
