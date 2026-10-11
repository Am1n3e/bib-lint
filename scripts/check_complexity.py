"""Enforce Ruff C901 with explicit ceilings for existing complex functions."""

import ast
import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(".github/complexity-baseline.json")


def function_names(source):
    """Map definition lines to names, including enclosing classes/functions."""
    names = {}

    def visit(node, parents):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            parents = (*parents, node.name)
            if not isinstance(node, ast.ClassDef):
                names[node.lineno] = ".".join(parents)
        for child in ast.iter_child_nodes(node):
            visit(child, parents)

    visit(ast.parse(source), ())
    return names


def scan(root):
    """Use Ruff's configured discovery and complexity calculation, ignoring noqa."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            ".",
            "--select",
            "C901",
            "--ignore-noqa",
            "--output-format",
            "json",
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        raise ValueError(f"Ruff failed: {result.stderr.strip()}")
    current = {}
    for finding in json.loads(result.stdout):
        match = re.fullmatch(r"`.+` is too complex \((\d+) > (\d+)\)", finding["message"])
        if finding["code"] != "C901" or match is None:
            raise ValueError(f"Unexpected Ruff diagnostic: {finding}")
        path = Path(finding["filename"])
        name = function_names(path.read_text())[finding["location"]["row"]]
        key = f"{path.relative_to(root).as_posix()}::{name}"
        if key in current:
            raise ValueError(f"Duplicate function identity: {key}")
        current[key] = int(match[1])
    return current


def compare(current, baseline):
    """Allow existing ceilings, reject new/increased violations and stale entries."""
    problems = []
    for name, score in sorted(current.items()):
        ceiling = baseline.get(name)
        if ceiling is None:
            problems.append(f"{name}: new complexity violation ({score}); refactor to the limit")
        elif score > ceiling:
            problems.append(f"{name}: complexity increased ({score} > baseline {ceiling})")
    for name in sorted(baseline.keys() - current.keys()):
        problems.append(f"{name}: resolved or removed; delete its baseline entry")
    return problems


def main(root=ROOT):
    try:
        config = tomllib.loads((root / "pyproject.toml").read_text())
        limit = config["tool"]["ruff"]["lint"]["mccabe"]["max-complexity"]
        baseline = json.loads((root / BASELINE).read_text())
        if baseline["max_complexity"] != limit:
            raise ValueError("Baseline and Ruff complexity limits differ")
        ceilings = baseline["functions"]
        if not isinstance(ceilings, dict) or any(
            type(score) is not int or score <= limit for score in ceilings.values()
        ):
            raise ValueError("Baseline ceilings must be integer complexities above the limit")
        problems = compare(scan(root), ceilings)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError) as error:
        print(f"Complexity check failed: {error}", file=sys.stderr)
        return 2
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    print(f"Complexity passed: limit {limit}; {len(ceilings)} existing function ceilings checked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
