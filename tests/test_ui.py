import json

import pytest
from provider_support import fixture_registry
from streamlit.testing.v1 import AppTest
from support import FakeClient, viewer_main

from bib_lint.audit import Workspace, run_audit
from bib_lint.storage import write_json
from bib_lint.viewer.jobs import Job, command_for


def button(app, key):
    return next(b for b in app.button if b.key == key)


def input_field(app, key):
    return next(t for t in app.text_input if t.key == key)


@pytest.fixture
def ui(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return AppTest.from_function(viewer_main, default_timeout=10).run()


def test_empty_startup_invalid_paths_and_parse_scope(ui, tmp_path):
    assert not ui.exception and not ui.error
    assert button(ui, "parse_preview") and button(ui, "verify_audit")
    button(ui, "parse_preview").click().run()
    assert "local bibliography" in ui.error[0].value
    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}\n@book{B,title={Two}}")
    aux = tmp_path / "paper.aux"
    aux.write_text(r"\citation{A,missing}")
    input_field(ui, "bib_input").set_value(str(bib))
    input_field(ui, "aux_input").set_value(str(aux))
    button(ui, "parse_preview").click().run()
    assert not ui.exception and not ui.error
    report = json.loads((tmp_path / "refs.bib-lint/report.tmp.json").read_text())
    assert report["verification_scope"]["eligible_keys"] == ["A"]
    assert "verification_run" not in report
    assert any("missing" in w.value for w in ui.warning)
    assert next(m for m in ui.metric if m.label == "Progress").value == "0/1"
    assert not (tmp_path / "refs.bib-lint/cache").exists()


def test_unknown_usage_metrics_and_directory_open(ui, tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}\n@book{B,title={Two}}")
    workspace, report, _ = run_audit(bib, preview=True)
    input_field(ui, "output_input").set_value(str(workspace.root))
    button(ui, "open_audit").click().run()
    assert not ui.exception and not ui.error
    metrics = {m.label: m.value for m in ui.metric}
    assert metrics["Used"] == "Unknown" and metrics["Progress"] == "0/2"
    assert metrics["Skipped"] == "0/2"
    # The active checkpoint wins over any older final on refresh.
    report["items"][0]["validations"]["correctness"] = {
        "complete": True,
        "is_correct": True,
        "methods": [],
    }
    write_json(workspace.checkpoint, report)
    ui.run()
    assert next(m for m in ui.metric if m.label == "Progress").value == "1/2"


class UIRegistry:
    def __init__(self):
        self.jobs = {}
        self.starts = []
        self.stops = []

    def find(self, root, owner=None):
        return self.jobs.get(str(root))

    def start(self, source, *, output=None, owner, **options):
        workspace, _, _ = run_audit(source, output=output, aux=options.get("aux"), preview=True)
        if any(job.state in {"running", "stopping"} for job in self.jobs.values()):
            raise ValueError("already running")
        self.starts.append(options)
        job = Job(workspace, command_for(source, workspace, **options), {owner})
        self.jobs[str(workspace.root)] = job
        return job

    def stop(self, job):
        self.stops.append(job.id)
        job.state = "stopping"


@pytest.fixture
def registry(monkeypatch):
    registry = UIRegistry()
    monkeypatch.setattr("bib_lint.viewer.controls.REGISTRY", registry)
    return registry


def test_direct_verify_rerun_stop_resume_and_refresh(ui, registry, tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}")
    input_field(ui, "bib_input").set_value(str(bib))
    button(ui, "verify_audit").click().run()
    assert not ui.exception and len(registry.starts) == 1
    assert button(ui, "verify_audit").disabled and button(ui, "parse_preview").disabled
    assert not button(ui, "stop_audit").disabled
    ui.run()
    assert len(registry.starts) == 1
    job = next(iter(registry.jobs.values()))
    ui.query_params["key"] = "A"
    ui.run()
    assert ui.header[0].value == "A" and len(registry.starts) == 1
    button(ui, "stop_audit").click().run()
    assert registry.stops == [job.id] and job.state == "stopping"
    assert button(ui, "stop_audit").disabled and not any(b.key == "resume_audit" for b in ui.button)
    job.state = "interrupted"
    ui.run()
    button(ui, "resume_audit").click().run()
    assert len(registry.starts) == 2 and not registry.starts[-1].get("refresh")
    job = next(iter(registry.jobs.values()))
    job.state = "completed"
    ui.query_params.clear()
    ui.run()
    input_field(ui, "key_input").set_value("a").run()
    button(ui, "refresh_key").click().run()
    assert registry.starts[-1].get("refresh") and registry.starts[-1]["citation_key"] == "a", (
        [e.value for e in ui.error],
        [(b.key, b.disabled) for b in ui.button],
        registry.starts,
    )
    job = next(iter(registry.jobs.values()))
    job.state = "interrupted"
    ui.run()
    button(ui, "resume_audit").click().run()
    assert not registry.starts[-1].get("refresh") and registry.starts[-1]["citation_key"] == "a"


def test_launch_failure_visible_without_created_report(ui, registry, tmp_path, monkeypatch):
    def fail(source, *, output=None, owner, **options):
        workspace = Workspace.for_input(source, output)
        job = Job(
            workspace,
            command_for(source, workspace, **options),
            {owner},
            state="failed",
            error="Could not launch",
        )
        registry.jobs[str(workspace.root)] = job
        return job

    monkeypatch.setattr(registry, "start", fail)
    input_field(ui, "bib_input").set_value(str(tmp_path / "missing.bib"))
    button(ui, "verify_audit").click().run()
    assert not ui.exception
    assert any("Could not launch" in e.value for e in ui.error)
    assert button(ui, "resume_audit")


def test_resume_saved_audit_and_key_eligibility(ui, registry, tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}\n@book{B,title={Two}}")
    aux = tmp_path / "paper.aux"
    aux.write_text(r"\citation{A}")
    workspace, _, _ = run_audit(bib, aux=aux, preview=True)
    input_field(ui, "output_input").set_value(str(workspace.root))
    button(ui, "open_audit").click().run()
    button(ui, "resume_saved").click().run()
    assert not ui.exception and registry.starts[-1]["aux"] == str(aux)
    # Invalid selected keys fail in shared orchestration without replacing saved bytes.
    before = workspace.checkpoint.read_bytes()
    with pytest.raises(ValueError, match="unused"):
        run_audit(bib, aux=aux, citation_key="B", client=FakeClient(), methods=fixture_registry({}))
    assert workspace.checkpoint.read_bytes() == before


@pytest.mark.parametrize(
    "content_type, raw",
    [
        ("application/json", b'{"saved": true}'),
        ("application/xml", b"<feed><title>Saved response</title></feed>"),
        ("text/html", b"<html>Saved response</html>"),
    ],
)
def test_cached_response_views_and_integrity(ui, tmp_path, content_type, raw):
    import httpx

    from bib_lint.verification.cache import ResponseCache

    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}")
    workspace, _, _ = run_audit(bib, preview=True)
    entry = ResponseCache(workspace.cache).save(
        "A",
        "publisher",
        "request",
        "https://jmlr.org/paper",
        httpx.Response(200, content=raw, headers={"Content-Type": content_type}),
    )
    input_field(ui, "output_input").set_value(str(workspace.root))
    button(ui, "open_audit").click().run()
    ui.query_params["key"] = "A"
    ui.run()
    assert not ui.exception and not ui.error
    assert any("SHA-256 verified" in c.value for c in ui.caption)
    if content_type == "application/json":
        assert any("saved" in j.value for j in ui.json)
    else:
        assert any("Saved response" in c.value for c in ui.code)
    path = workspace.cache / entry["path"]
    path.write_bytes(b"corrupted")
    ui.run()
    assert not ui.exception and any("Checksum" in e.value for e in ui.error)
    assert path.read_bytes() == b"corrupted"


def test_new_session_reattaches_to_running_workspace(ui, registry, tmp_path):
    bib = tmp_path / "refs.bib"
    bib.write_text("@book{A,title={One}}")
    job = registry.start(bib, owner="previous-browser")
    input_field(ui, "output_input").set_value(str(job.workspace.root))
    button(ui, "open_audit").click().run()
    assert not ui.exception and button(ui, "verify_audit").disabled
    assert button(ui, "stop_audit") and len(registry.starts) == 1
    ui.run()
    assert len(registry.starts) == 1


def test_open_invalid_and_unknown_detail(ui, tmp_path):
    input_field(ui, "output_input").set_value(str(tmp_path / "missing"))
    button(ui, "open_audit").click().run()
    assert any("existing audit directory" in e.value for e in ui.error)
    bib = tmp_path / "empty.bib"
    bib.write_text("%empty")
    workspace, _, _ = run_audit(bib, preview=True)
    input_field(ui, "output_input").set_value(str(workspace.root))
    button(ui, "open_audit").click().run()
    ui.query_params["key"] = "missing"
    ui.run()
    assert any("key not found" in e.value for e in ui.error)
    next(b for b in ui.button if b.label == "All references").click().run()
    assert not ui.error


def test_generic_provider_revision_scope_and_extension_display(tmp_path, monkeypatch):
    from provider_support import FixtureProvider

    from bib_lint.verification.providers import METHODS
    from bib_lint.verification.providers.protocol import LookupAttempt, LookupResult

    bib = tmp_path / "refs.bib"
    bib.write_text("@article{Example,title={An Example Paper},author={Jane Smith},year={2025}}")
    payload = {
        "heading": "An Example Paper",
        "people": [{"given": "Jane", "family": "Smith"}],
        "date": "2025",
    }
    providers = [FixtureProvider(name, payload=payload) for name in METHODS]

    def incomplete(*_):
        return LookupResult(
            attempts=(LookupAttempt("catalog", "volume 2025", complete=False),),
            complete=False,
            diagnostic="Page budget exhausted",
        )

    providers.append(FixtureProvider("extension", version="2", lookup=incomplete))
    workspace, _, _ = run_audit(bib, methods=providers, client=FakeClient())
    monkeypatch.chdir(tmp_path)
    app = AppTest.from_function(viewer_main, default_timeout=10).run()
    input_field(app, "output_input").set_value(str(workspace.root))
    button(app, "open_audit").click().run()
    app.query_params["key"] = "Example"
    app.run()
    assert not app.exception
    rows = next(frame.value for frame in app.dataframe if "Source" in frame.value.columns)
    assert set(rows["Source"]) == set(METHODS) | {"extension"}
    extension = rows[rows["Source"] == "extension"].iloc[0]
    assert extension["Revision"] == "2" and extension["Search scope"] == "volume 2025"
    assert extension["Error"] == "Page budget exhausted"
    raw = next(value.value for value in app.json if "extension" in value.value)
    assert "incomplete_search" in raw
