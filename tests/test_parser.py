import hashlib
import json

import pytest

from bib_lint import BibliographyParseError, parse_file, parse_string
from bib_lint.cli import main

SOURCE = r"""% Original comment
@string{venue = "Journal of " # "Examples"}
@preamble{"\newcommand{\noop}[1]{}"}
@ARTICLE{MixedCase2026,
 author = {de la Cruz, Jr., Juan Carlos and {Research and Development Group}
           and Garc{\'i}a, Ana and others},
 editor = {Wang, Zora Zhiruo},
 title = {A {LaTeX} title with {nested {braces}}},
 journal = venue,
 month = jan,
 customfield = "Keep this",
 crossref = {Proceedings2026}
}
@proceedings{Proceedings2026, title={Proceedings}, year=2026}
"""


def test_fields_keys_order_and_source():
    result = parse_string(SOURCE)
    assert list(result.entries) == ["MixedCase2026", "Proceedings2026"]
    entry = result.entries["MixedCase2026"]
    assert entry.type == "article"
    assert entry.fields["title"] == "A {LaTeX} title with {nested {braces}}"
    assert entry.fields["customfield"] == "Keep this"
    assert entry.fields["crossref"] == "Proceedings2026"
    assert "year" not in entry.fields  # Cross-reference inheritance is not applied.
    assert result.source_text == SOURCE
    assert result.source_sha256 == hashlib.sha256(SOURCE.encode()).hexdigest()


def test_names_and_roles():
    entry = parse_string(SOURCE).entries["MixedCase2026"]
    author, group, accented, others = entry.persons["author"]
    assert (author.first, author.middle, author.prelast, author.last, author.lineage) == (
        ("Juan",),
        ("Carlos",),
        ("de", "la"),
        ("Cruz",),
        ("Jr.",),
    )
    assert group.kind == "literal"
    assert group.bibtex == "{Research and Development Group}"
    assert accented.last == (r"Garc{\'i}a",)
    assert others.kind == "others"
    editor = entry.persons["editor"][0]
    assert editor.first == ("Zora",)
    assert editor.middle == ("Zhiruo",)


def test_macros_and_preambles():
    result = parse_string(SOURCE)
    assert result.entries["MixedCase2026"].fields["journal"] == "Journal of Examples"
    assert result.entries["MixedCase2026"].fields["month"] == "January"
    assert result.preambles == (r"\newcommand{\noop}[1]{}",)
    with pytest.raises(BibliographyParseError):
        parse_string("@book{x, title=venue}")  # Macro state must not leak between inputs.


@pytest.mark.parametrize(
    "source",
    [
        "@article{x, title={bad}",
        "@article{x,title={a}}\n@book{X,title={b}}",
        "@book{x,title={a},TITLE={b}}",
        "@book{x,title=undefinedmacro}",
        "@book{x,author={a,b,c,d}}",
    ],
)
def test_invalid_input_reports_source(source):
    with pytest.raises(BibliographyParseError) as error:
        parse_string(source, source_name="input.bib")
    assert error.value.source == "input.bib"
    assert "input.bib" in str(error.value)


def test_syntax_error_line():
    with pytest.raises(BibliographyParseError) as error:
        parse_string("\n\n@book{x,title=undefinedmacro}")
    assert error.value.line == 3


def test_encoding_and_original_bytes(tmp_path):
    path = tmp_path / "input.bib"
    raw = "@book{x, title={Café}}\r\n".encode("latin-1")
    path.write_bytes(raw)
    with pytest.raises(BibliographyParseError):
        parse_file(path)
    result = parse_file(path, encoding="latin-1")
    assert result.source_text == raw.decode("latin-1")
    assert result.source_sha256 == hashlib.sha256(raw).hexdigest()
    assert path.read_bytes() == raw


def test_empty_input_and_serialization():
    result = parse_string("% No entries\n")
    assert result.entries == {}
    assert result.to_dict()["summary"]["total_count"] == 0
    assert "source_text" not in result.to_dict()
    assert result.to_dict(include_source=True)["source_text"] == "% No entries\n"


def test_cli_json(tmp_path, capsys):
    path = tmp_path / "input.bib"
    path.write_text(SOURCE)
    assert main(["parse", str(path), "--include-source"]) == 0
    output = capsys.readouterr()
    data = json.loads(path.with_suffix(".tmp.json").read_text())
    assert "Parsing:" in output.out
    assert "total entries found: 2; errors: 0" in output.out
    assert output.err == ""
    assert data["schema_version"] == 2
    assert data["summary"]["total_count"] == 2
    assert data["items"][0]["entry"]["key"] == "MixedCase2026"
    assert data["source_text"] == SOURCE
    assert data["summary"]["total_not_used"] is None
    assert all(item["validations"] == {} for item in data["items"])
    assert path.read_text() == SOURCE


@pytest.mark.parametrize("mode", ["missing", "invalid", "encoding"])
def test_cli_failures_have_no_partial_json(tmp_path, capsys, mode):
    path = tmp_path / "input.bib"
    args = ["parse", str(path)]
    if mode == "invalid":
        path.write_text("@book{ok,title={Good}}\n@book{bad,title=unknown}")
    elif mode == "encoding":
        path.write_text(SOURCE)
        args += ["--encoding", "not-a-codec"]
    assert main(args) == 2
    output = capsys.readouterr()
    assert "total entries found: unknown" in output.out
    assert "errors: 1; JSON not written" in output.out
    assert not path.with_suffix(".tmp.json").exists()
    assert output.err.startswith("Error: ")
    assert "Traceback" not in output.err


def test_cli_custom_output_and_failed_parse_preserves_previous_json(tmp_path, capsys):
    source = tmp_path / "input.bib"
    destination = tmp_path / "report.tmp.json"
    source.write_text(SOURCE)
    assert main(["parse", str(source), "-o", str(destination)]) == 0
    previous = destination.read_bytes()
    assert json.loads(previous)["summary"]["total_count"] == 2
    source.write_text("@book{x,title=undefinedmacro}")
    assert main(["parse", str(source), "--output", str(destination)]) == 2
    assert destination.read_bytes() == previous


@pytest.mark.parametrize("alias", ["same", "symlink", "hardlink"])
def test_cli_cannot_overwrite_input(tmp_path, alias, capsys):
    source = tmp_path / "input.bib"
    source.write_text(SOURCE)
    destination = source if alias == "same" else tmp_path / "alias.json"
    if alias == "symlink":
        destination.symlink_to(source)
    elif alias == "hardlink":
        destination.hardlink_to(source)
    assert main(["parse", str(source), "-o", str(destination)]) == 2
    assert source.read_text() == SOURCE
    assert "must not overwrite" in capsys.readouterr().err


def test_cli_output_failure_reports_parsed_count(tmp_path, capsys):
    source = tmp_path / "input.bib"
    source.write_text(SOURCE)
    destination = tmp_path / "missing" / "report.json"
    assert main(["parse", str(source), "-o", str(destination)]) == 2
    assert "total entries found: 2; errors: 1" in capsys.readouterr().out


def test_cli_empty_bibliography(tmp_path, capsys):
    source = tmp_path / "empty.bib"
    source.write_text("% empty")
    assert main(["parse", str(source)]) == 0
    assert "total entries found: 0; errors: 0" in capsys.readouterr().out
    assert json.loads(source.with_suffix(".tmp.json").read_text())["items"] == []
