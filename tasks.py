"""Local development tasks, run with ``uv run invoke <task>``."""

import shlex
import shutil
from pathlib import Path

from invoke import Collection, Exit, task

ROOT = Path(__file__).resolve().parent
OPENSPEC_VERSION = "1.14.1"


@task(help={"openspec": "Initialize local OpenSpec planning and generated Codex skills."})
def dev_init(context, openspec=True):
    """Sync development dependencies, install Git hooks, and initialize local tooling."""
    with context.cd(str(ROOT)):
        context.run("uv sync --locked --group dev", echo=True)
        context.run("uv run --locked lefthook install pre-push", echo=True)
        if not openspec:
            return
        if not shutil.which("node") or not shutil.which("npx"):
            raise Exit(
                "OpenSpec needs Node.js 20.19+ and npm; use dev_init --no-openspec to skip it."
            )
        version = context.run("node --version", hide=True).stdout.strip().removeprefix("v")
        if tuple(int(part) for part in version.split(".")[:2]) < (20, 19):
            raise Exit("OpenSpec needs Node.js 20.19+; use dev_init --no-openspec to skip it.")
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


BENCHMARK_HELP = {
    "name": "Dataset: all, hallmark, zenodo, gptzero, or hallucitation.",
    "root": (
        "Artifact directory; defaults to evaluation/.artifacts. "
        "Use a fresh root after code changes."
    ),
}
SPLIT_HELP = "One official split; requires a single benchmark. Defaults to every split."


def _benchmark_python(context, module, arguments, root):
    command = ["uv", "run", "--locked", "--group", "benchmark", "python", "-m", module]
    command.extend(arguments)
    if root:
        command.extend(["--root", root])
    with context.cd(str(ROOT)):
        context.run(shlex.join(command), echo=True)


def _benchmark_harness(context, command, benchmark, split, root, extra=()):
    arguments = [command, "--benchmark", benchmark]
    if split:
        arguments.extend(["--split", split])
    arguments.extend(extra)
    _benchmark_python(context, "evaluation.harness", arguments, root)


@task(help={**BENCHMARK_HELP, "name": BENCHMARK_HELP["name"] + " Defaults to all."})
def benchmark_init(context, name="all", root=""):
    """Install the locked benchmark scorer and download or verify frozen datasets."""
    with context.cd(str(ROOT)):
        context.run("uv sync --locked --group benchmark", echo=True)
    _benchmark_harness(context, "prepare", name, "", root)


@task(
    positional=["name"],
    help={
        **BENCHMARK_HELP,
        "split": SPLIT_HELP,
        "limit": "First N cases per split for a partial smoke run; 0 means the full dataset.",
        "workers": "Concurrent references with shared host pacing (default: 8).",
        "retry_errors": "Retry failed cases and provider errors when resuming.",
        "verbose": "Print provider progress while auditing references.",
    },
)
def benchmark_run(
    context,
    name,
    split="",
    root="",
    limit=0,
    workers=8,
    retry_errors=False,
    verbose=False,
):
    """Run or resume live reference audits and score the selected benchmarks."""
    extra = ["--workers", str(workers)]
    if limit:
        extra.extend(["--limit", str(limit)])
    if retry_errors:
        extra.append("--retry-errors")
    if verbose:
        extra.append("--verbose")
    _benchmark_harness(context, "run", name, split, root, extra)


@task(positional=["name"], help={**BENCHMARK_HELP, "split": SPLIT_HELP})
def benchmark_score(context, name, split="", root=""):
    """Rescore saved predictions without contacting metadata providers."""
    _benchmark_harness(context, "score", name, split, root)


@task(help={"root": BENCHMARK_HELP["root"]})
def benchmark_verify(context, root=""):
    """Verify every benchmark and export baseline results after full completion."""
    _benchmark_python(context, "scripts.check_baseline", [], root)


ns = Collection(dev_init, lint, format_check, format_code, complexity, check)
ns.add_collection(
    Collection(
        "benchmark",
        init=benchmark_init,
        run=benchmark_run,
        score=benchmark_score,
        verify=benchmark_verify,
    )
)
