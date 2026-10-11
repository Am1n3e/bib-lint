"""Local workflow widgets; execution lives in the shared audit and job layers."""

import uuid
from pathlib import Path

import streamlit as st

from bib_lint.audit import audit_summary, run_audit
from bib_lint.viewer.data import load_report
from bib_lint.viewer.jobs import ACTIVE, REGISTRY


def remember_input(key):
    st.session_state[f"saved_{key}"] = st.session_state[key]


def path_input(label, key, **kwargs):
    # Retain values when disabled widgets are recreated during a job transition.
    st.session_state[key] = st.session_state.get(f"saved_{key}", "")
    return st.text_input(
        label,
        key=key,
        on_change=remember_input,
        args=(key,),
        **kwargs,
    )


def start_from_command(job, owner):
    """Resume immutable original inputs/key while removing the one-shot refresh."""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("--output")
    parser.add_argument("--aux")
    parser.add_argument("--encoding")
    parser.add_argument("--key")
    parser.add_argument("--include-source", action="store_true")
    parser.add_argument("--refresh", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(job.command[4:])
    return REGISTRY.start(
        args.source,
        output=args.output,
        owner=owner,
        aux=args.aux,
        encoding=args.encoding,
        include_source=args.include_source,
        citation_key=args.key,
        verbose=args.verbose,
    )


@st.fragment(run_every=1)
def job_status(root):
    job = REGISTRY.find(root)
    if job is None:
        return
    snapshot = job.snapshot()
    st.caption(f"Audit job: {snapshot['state']}")
    if snapshot["error"]:
        st.error(snapshot["error"])
    if snapshot["logs"]:
        with st.expander("Verification diagnostics"):
            st.code("".join(snapshot["logs"]), language="text")
    try:
        report = load_report(root)
        counts = audit_summary(report)
        eligible = counts["eligible"]
        st.progress(
            counts["completed"] / eligible if eligible else 1.0,
            text=f"{counts['completed']}/{eligible} eligible entries completed",
        )
        active = job.workspace.active()
        signature = (snapshot["state"], active.stat().st_mtime_ns)
    except (OSError, ValueError, KeyError, TypeError):
        signature = (snapshot["state"], None)
    key = f"job_signature_{job.id}"
    old = st.session_state.get(key)
    st.session_state[key] = signature
    if old is not None and old != signature:
        st.rerun()  # Follow source checkpoints and promotion in the evidence views.


def workflow_controls():
    owner = st.session_state.setdefault("audit_owner", uuid.uuid4().hex)
    selected = st.session_state.get("report_path", "")
    job = None
    if selected and Path(selected).is_dir():
        job = REGISTRY.find(selected, owner)
    active_root = st.session_state.get("active_root")
    active_job = REGISTRY.find(active_root, owner) if active_root else None
    if active_job and (active_job.state in ACTIVE or selected == str(active_job.workspace.root)):
        job = active_job
    busy = job is not None and job.state in ACTIVE
    with st.expander("Local audit workflow", expanded=not selected):
        bib = path_input("Bibliography path", key="bib_input", disabled=busy)
        aux = path_input("Compiled AUX path (optional)", key="aux_input", disabled=busy)
        output = path_input(
            "Output / existing audit directory",
            key="output_input",
            disabled=busy,
            help="Blank output defaults to <bibliography-stem>.bib-lint beside the input.",
        )
        key = path_input("Citation key (optional)", key="key_input", disabled=busy)
        options = dict(aux=aux or None, citation_key=key or None)
        parse_column, verify_column, open_column = st.columns(3)
        parse = parse_column.button("Parse", disabled=busy, key="parse_preview")
        verify = verify_column.button("Verify", disabled=busy, key="verify_audit")
        opened = open_column.button("Open audit directory", disabled=busy, key="open_audit")
        full, selected_column = st.columns(2)
        refresh = full.button("Refresh", disabled=busy, key="refresh_audit")
        verify_key = selected_column.button(
            "Verify selected key", disabled=busy or not key, key="verify_key"
        )
        refresh_key = selected_column.button(
            "Refresh selected key", disabled=busy or not key, key="refresh_key"
        )
        job = _workflow_action(
            opened,
            output,
            parse,
            verify,
            refresh,
            verify_key,
            refresh_key,
            bib,
            aux,
            key,
            owner,
            options,
            job,
        )
        for warning in st.session_state.get("preview_warnings", []):
            st.warning(warning)
        _job_controls(job, selected, owner)
    return busy


def _workflow_action(
    opened,
    output,
    parse,
    verify,
    refresh,
    verify_key,
    refresh_key,
    bib,
    aux,
    key,
    owner,
    options,
    job,
):
    try:
        if opened:
            path = Path(output).absolute()
            if not output or not path.is_dir():
                raise ValueError("Enter an existing audit directory")
            load_report(path)
            st.session_state["report_path"] = str(path)
            st.rerun()
        if parse or verify or refresh or verify_key or refresh_key:
            if not bib:
                raise ValueError("Enter a local bibliography path")
            if parse:
                workspace, _, warnings = run_audit(
                    bib, output=output or None, aux=aux or None, preview=True
                )
                st.session_state["preview_warnings"] = warnings
            else:
                # Full-scope actions ignore the optional key; key actions select it explicitly.
                options["citation_key"] = key if verify_key or refresh_key else None
                job = REGISTRY.start(
                    bib,
                    output=output or None,
                    owner=owner,
                    refresh=refresh or refresh_key,
                    **options,
                )
                workspace = job.workspace
                st.session_state["active_root"] = str(workspace.root)
            st.session_state["report_path"] = str(workspace.root)
            st.rerun()
    except (OSError, ValueError, LookupError) as exc:
        st.error(str(exc))
    return job


def _job_controls(job, selected, owner):
    if job:
        if job.state in ACTIVE:
            if st.button("Stop", disabled=job.state == "stopping", key="stop_audit"):
                REGISTRY.stop(job)
                st.rerun()
        elif job.state in {"interrupted", "failed", "completed"}:
            if st.button("Resume", key="resume_audit"):
                try:
                    job = start_from_command(job, owner)
                    st.session_state["active_root"] = str(job.workspace.root)
                    st.rerun()
                except (OSError, ValueError) as exc:
                    st.error(str(exc))
        job_status(str(job.workspace.root))
    elif selected and Path(selected).is_dir():
        # Reopen an audit from a previous server process; resume its recorded input.
        _resume_saved(selected, owner)


def _resume_saved(selected, owner):
    if st.button("Resume", key="resume_saved"):
        try:
            report = load_report(selected)
            saved = report.get("audit_input")
            if not saved:
                raise ValueError(
                    "Enter the original input path and use Verify to resume this audit"
                )
            options = {k: saved[k] for k in ("aux", "encoding", "include_source") if k in saved}
            job = REGISTRY.start(saved["path"], output=selected, owner=owner, **options)
            st.session_state["active_root"] = str(job.workspace.root)
            st.rerun()
        except (OSError, ValueError, KeyError) as exc:
            st.error(str(exc))
