import copy
import json

import pytest
from streamlit.testing.v1 import AppTest
from support import viewer_main

from bib_lint.viewer import app as viewer_app
from bib_lint.viewer.agent import attach_reviews, entry_digest, sidecar_path
from bib_lint.viewer.data import comparison_rows, load_report, suggestions, table_rows


def fixture(tmp_path):
    entry = {"key": "sample", "type": "article", "fields": {"title": "Wrong"}, "persons": {}}
    report = {
        "items": [
            {
                "entry": entry,
                "validations": {
                    "is_used": True,
                    "correctness": {"is_correct": True, "complete": True, "methods": []},
                },
            }
        ]
    }
    review = {
        "citation_key": "sample",
        "entry_sha256": entry_digest(entry),
        "status": "Invalid",
        "summary": "Title differs",
        "reviewed_at": "2026-09-26",
        "checked_fields": ["title"],
        "evidence": [{"url": "https://example.org/paper", "supports": "Title is Right"}],
        "comparisons": [
            {"field": "title", "input": "Wrong", "found": "Right", "result": "mismatch"}
        ],
    }
    report_path = tmp_path / "references.json"
    report_path.write_text(json.dumps(report))
    sidecar = sidecar_path(report_path)
    sidecar.write_text(json.dumps({"schema_version": 1, "source": "agent", "items": [review]}))
    return report_path, sidecar


def test_overlay_never_changes_automated_results_or_files(tmp_path):
    path, sidecar = fixture(tmp_path)
    before = path.read_bytes(), sidecar.read_bytes()
    report = load_report(path)
    validations = copy.deepcopy(report["items"][0]["validations"])
    assert attach_reviews(report, sidecar) == []
    assert report["items"][0]["validations"] == validations
    row = table_rows(report)[0]
    assert row["Status"] == "Correct" and row["Agent"] == "Invalid"
    assert row["Found"] == row["Consensus"] == "0/0"
    assert suggestions(report["items"][0])[0]["Source"] == "agent"
    assert comparison_rows(report["items"][0])[0]["Status"] == "Mismatch"
    assert before == (path.read_bytes(), sidecar.read_bytes())
    assert sidecar_path(tmp_path / "references.tmp.json") == sidecar


def test_changed_entry_quarantines_stale_evidence(tmp_path):
    path, sidecar = fixture(tmp_path)
    report = load_report(path)
    report["items"][0]["entry"]["fields"]["title"] = "Edited"
    assert "stale" in attach_reviews(report, sidecar)[0]
    assert "agent_review" not in report["items"][0]
    assert not suggestions(report["items"][0])
    assert table_rows(report)[0]["Agent"] == "Not checked"


@pytest.mark.parametrize("bad", ["duplicate", "url", "status", "comparison"])
def test_malformed_evidence_rejected_before_attachment(tmp_path, bad):
    path, sidecar = fixture(tmp_path)
    data = json.loads(sidecar.read_text())
    item = data["items"][0]
    if bad == "duplicate":
        data["items"].append(item)
    elif bad == "url":
        item["evidence"][0]["url"] = "javascript:alert(1)"
    elif bad == "status":
        item["status"] = "Invented"
    else:
        item["comparisons"][0]["result"] = "Invented"
    sidecar.write_text(json.dumps(data))
    report = load_report(path)
    with pytest.raises(ValueError):
        attach_reviews(report, sidecar)
    assert "agent_review" not in report["items"][0]


@pytest.mark.parametrize("entrypoint", ["function", "file"])
def test_agent_ui_and_automated_metrics(tmp_path, monkeypatch, entrypoint):
    fixture(tmp_path)
    monkeypatch.chdir(tmp_path)
    app = (
        AppTest.from_file(viewer_app.__file__)
        if entrypoint == "file"
        else AppTest.from_function(viewer_main)
    ).run()
    assert not app.exception
    assert app.dataframe[0].value.iloc[0]["Agent"] == ["Invalid"]
    assert next(m for m in app.metric if m.label == "Correct").value == "1/1"
    app.toggle[1].set_value(True).run()
    assert len(app.dataframe[0].value) == 1  # Agent error retained despite automated pass.
    app.query_params["key"] = "sample"
    app.run()
    assert not app.exception
    assert app.tabs[-1].label == "Agent evidence"
    assert "agent" in list(app.dataframe[-1].value["Source"])
