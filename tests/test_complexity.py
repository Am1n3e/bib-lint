"""Quality gate regression tests; no network or project runtime required."""

import json

from scripts.check_complexity import BASELINE, compare, function_names, main, scan


def test_baseline_allows_existing_or_lower_complexity_but_rejects_growth():
    assert compare({"existing": 12}, {"existing": 12}) == []
    assert compare({"existing": 11}, {"existing": 12}) == []
    assert "increased" in compare({"existing": 13}, {"existing": 12})[0]


def test_new_violation_and_obsolete_baseline_fail():
    assert "new complexity violation" in compare({"new": 11}, {})[0]
    assert "delete its baseline entry" in compare({}, {"removed": 12})[0]


def test_function_identity_preserves_class_and_nested_scopes():
    names = function_names(
        "class First:\n def load(self):\n  def nested(): pass\n"
        "class Second:\n async def load(self): pass\n"
    )
    assert names == {2: "First.load", 3: "First.load.nested", 5: "Second.load"}


def quality_project(tmp_path, ceilings):
    (tmp_path / "pyproject.toml").write_text("[tool.ruff.lint.mccabe]\nmax-complexity = 10\n")
    (tmp_path / BASELINE).parent.mkdir()
    (tmp_path / BASELINE).write_text(json.dumps({"max_complexity": 10, "functions": ceilings}))
    branches = "".join(f"    if value == {n}: return {n}\n" for n in range(11))
    (tmp_path / "example.py").write_text("def complex(value):  # noqa: C901\n" + branches)
    return tmp_path


def test_real_ruff_ignores_suppressions_and_cli_rejects_new_violation(tmp_path, capsys):
    root = quality_project(tmp_path, {})
    assert scan(root) == {"example.py::complex": 12}
    assert main(root) == 1
    assert "new complexity violation" in capsys.readouterr().err


def test_real_ruff_accepts_baseline_then_rejects_growth(tmp_path, capsys):
    root = quality_project(tmp_path, {"example.py::complex": 12})
    assert main(root) == 0
    with (root / "example.py").open("a") as output:
        output.write("    if value == 20: return 20\n")
    assert main(root) == 1
    assert "13 > baseline 12" in capsys.readouterr().err


def test_ruff_failure_is_not_an_empty_success(tmp_path, capsys):
    root = quality_project(tmp_path, {})
    (root / "pyproject.toml").write_text(
        '[tool.ruff]\nrequired-version = "==0.0.1"\n[tool.ruff.lint.mccabe]\nmax-complexity = 10\n'
    )
    assert main(root) == 2
    assert "Ruff failed" in capsys.readouterr().err


def test_malformed_baseline_fails_closed(tmp_path, capsys):
    root = quality_project(tmp_path, {})
    (root / BASELINE).write_text('{"max_complexity":10,"functions":{"bad":true}}')
    assert main(root) == 2
    assert "integer complexities" in capsys.readouterr().err
