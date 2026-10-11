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
