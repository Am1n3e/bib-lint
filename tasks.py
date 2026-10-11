"""Local development tasks, run with ``uv run invoke <task>``."""

import shlex
import shutil
from pathlib import Path

from invoke import Exit, task

ROOT = Path(__file__).resolve().parent
OPENSPEC_VERSION = "1.14.1"


@task(help={"openspec": "Initialize local OpenSpec planning and generated Codex skills."})
def init(context, openspec=True):
    """Sync development dependencies and initialize ignored local tooling."""
    with context.cd(str(ROOT)):
        context.run("uv sync --group dev", echo=True)
        if not openspec:
            return
        if not shutil.which("node") or not shutil.which("npx"):
            raise Exit("OpenSpec needs Node.js 20.19+ and npm; use init --no-openspec to skip it.")
        version = context.run("node --version", hide=True).stdout.strip().removeprefix("v")
        if tuple(int(part) for part in version.split(".")[:2]) < (20, 19):
            raise Exit("OpenSpec needs Node.js 20.19+; use init --no-openspec to skip it.")
        context.run(
            shlex.join(
                [
                    "npx",
                    "--yes",
                    "--package",
                    f"@fission-ai/openspec@{OPENSPEC_VERSION}",
                    "openspec",
                    "init",
                    "--tools",
                    "codex",
                    "--no-animation",
                ]
            ),
            echo=True,
            env={"OPENSPEC_TELEMETRY": "0"},
        )


@task
def lint(context):
    """Check Python lint rules without modifying files."""
    with context.cd(str(ROOT)):
        context.run("ruff check .", echo=True)


@task
def format_check(context):
    """Check Ruff formatting without modifying files."""
    with context.cd(str(ROOT)):
        context.run("ruff format --check .", echo=True)


@task(name="format")
def format_code(context):
    """Apply Ruff formatting to Python files."""
    with context.cd(str(ROOT)):
        context.run("ruff format .", echo=True)


@task
def complexity(context):
    """Enforce a McCabe complexity ceiling of 10 for every Python function."""
    with context.cd(str(ROOT)):
        context.run("ruff check . --select C901 --ignore-noqa", echo=True)


@task(pre=[lint, format_check, complexity])
def check(context):
    """Run all code quality checks used by CI."""
