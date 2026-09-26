"""CLI presentation; parsing and JSON writing live in workflow.py."""

import argparse
import subprocess
import sys
from pathlib import Path

from bib_lint.verification import verify_file
from bib_lint.workflow import parse_bib


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="bib-lint", description="Parse BibTeX for reference auditing."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    parse = subcommands.add_parser(
        "parse", help="Parse BibTeX and optionally check compiled AUX usage"
    )
    parse.add_argument("path", help="Input .bib file (never modified)")
    parse.add_argument("--aux", type=Path, help="Compiled .aux file for citation usage")
    parse.add_argument(
        "-o", "--output", type=Path, help="Final report name (parse writes input stem.tmp.json)"
    )
    parse.add_argument("--encoding", default="utf-8", help="Input encoding (default: utf-8)")
    parse.add_argument(
        "--include-source", action="store_true", help="Include decoded original text"
    )
    verify = subcommands.add_parser(
        "verify", help="Verify parsed references against metadata providers"
    )
    verify.add_argument("path", help="Parsed JSON report")
    verify.add_argument("--key", help="Verify only this used citation key (case-insensitive)")
    verify.add_argument(
        "-o", "--output", type=Path, help="Final report name (default: remove .tmp from input name)"
    )
    verify.add_argument("--cache-dir", type=Path, default=Path(".bib-lint-cache"))
    verify.add_argument("--refresh", action="store_true", help="Ignore cached provider responses")
    verify.add_argument(
        "--verbose",
        action="store_true",
        help="Print full responses: formatted JSON or raw HTML/XML",
    )
    view = subcommands.add_parser("view", help="Open the Streamlit reference viewer")
    view.add_argument(
        "path", nargs="?", default="references.json", help="Report or checkpoint JSON"
    )
    view.add_argument("--cache-dir", type=Path, default=Path(".bib-lint-cache"))
    view.add_argument("--port", type=int, default=8501)
    args = parser.parse_args(argv)
    if args.command == "view":
        app = Path(__file__).parent / "viewer" / "app.py"
        try:
            return subprocess.call(
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(app),
                    "--server.headless",
                    "true",
                    "--server.address",
                    "127.0.0.1",
                    "--server.port",
                    str(args.port),
                    "--browser.gatherUsageStats",
                    "false",
                    "--",
                    "--report",
                    args.path,
                    "--cache-dir",
                    str(args.cache_dir),
                ]
            )
        except KeyboardInterrupt:
            return 130
    if args.command == "verify":
        try:
            destination, summary = verify_file(
                args.path,
                output=args.output,
                cache_dir=args.cache_dir,
                refresh=args.refresh,
                verbose=args.verbose,
                citation_key=args.key,
                progress=lambda message: print(message, flush=True),
            )
        except KeyboardInterrupt:
            print(
                "Interrupted; checkpoint retained. Rerun the same command to resume.",
                file=sys.stderr,
            )
            return 130
        except (OSError, ValueError, LookupError) as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        print("Verification summary: " + "; ".join(f"{k}: {v}" for k, v in summary.items()))
        print(f"output: {destination}")
        return 0

    print(f"Parsing: {args.path}", flush=True)
    if args.aux:
        print(f"Checking AUX citation usage: {args.aux}", flush=True)
    bib, aux = parse_bib(
        args.path,
        args.aux,
        output=args.output,
        encoding=args.encoding,
        include_source=args.include_source,
    )
    total = bib.total if bib.total is not None else "unknown (parsing did not complete)"
    status = "; JSON not written." if bib.error or (aux and aux.error) else ""
    print(
        f"Bib summary: total entries found: {total}; errors: {int(bib.error is not None)}{status}"
    )
    if bib.error:
        print(f"Error: {bib.error}", file=sys.stderr)
    if aux is not None:
        if aux.error:
            print(f"Error: {aux.error}", file=sys.stderr)
            print("AUX summary: errors: 1; usage incomplete; JSON not written.")
        else:
            print(
                f"AUX summary: unique explicit citation keys: {aux.total}; unused: {aux.unused}; "
                f"missing from bibliography: {len(aux.missing)}; errors: 0"
            )
            if aux.missing:
                print("Missing citation keys: " + ", ".join(aux.missing))
    else:
        print(
            "AUX summary: skipped" + (" (BibTeX step failed)." if args.aux else " (not supplied).")
        )
    if bib.error or (aux is not None and aux.error):
        return 2
    print(f"output: {bib.output}")
    return 0
