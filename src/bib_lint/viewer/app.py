"""Streamlit entry point. All UI uses built-in Streamlit components."""

import argparse
import json
import re
from pathlib import Path

import streamlit as st

from bib_lint.status import STATUS_COLORS
from bib_lint.verification.matching import input_record
from bib_lint.viewer.agent import attach_reviews, sidecar_path
from bib_lint.viewer.controls import workflow_controls
from bib_lint.viewer.data import (
    cache_entries,
    comparison_rows,
    display,
    load_report,
    pretty_xml,
    read_response,
    source_rows,
    suggestions,
    table_rows,
)


def status_rows(rows):
    """Native colored dataframe chips, without changing report values."""
    return [
        {**row, "Status": [row["Status"]], **({"Agent": [row["Agent"]]} if "Agent" in row else {})}
        for row in rows
    ]


def wrapped_status_rows(rows):
    # Escape metadata so Markdown renders the original text literally.
    return [
        {
            key: f":{STATUS_COLORS[value]}-badge[{value}]"
            if key == "Status"
            else re.sub(r"([\\`*_{}\[\]()<>#+.!|:$~-])", r"\\\1", str(value))
            for key, value in row.items()
        }
        for row in rows
    ]


def status_column(label="Status"):
    return st.column_config.MultiselectColumn(
        label, options=list(STATUS_COLORS), color=list(STATUS_COLORS.values()), disabled=True
    )


def overview(report):
    st.title("Bib-Lint")
    rows = table_rows(report)
    if any(i.get("agent_review") for i in report["items"]):
        reviewed = sum(bool(i.get("agent_review")) for i in report["items"])
        st.caption(
            f"Agent web review: {reviewed} references. Status, metrics and consensus "
            "below remain the automated results; Agent is a separate assessment."
        )
    total = len(rows)
    used_rows = [row for row in rows if row["Used in paper"] == "Yes"]
    used = len(used_rows)
    scope = report.get("verification_scope")
    eligible_rows = (
        [row for row in rows if row["Citation key"] in scope["eligible_keys"]]
        if scope
        else used_rows
    )
    eligible = len(eligible_rows)
    unknown_usage = any(row["Used in paper"] == "Unknown" for row in rows) or (
        scope and scope["mode"] == "all"
    )
    skipped = sum(row["Status"] == "Skipped" for row in rows)
    completed = sum(
        row["Status"] in {"Correct", "Invalid", "Unresolved", "Partial match", "Needs review"}
        for row in eligible_rows
    )
    correct = sum(row["Status"] == "Correct" for row in eligible_rows)
    invalid = sum(row["Status"] == "Invalid" for row in eligible_rows)
    unresolved = sum(row["Status"] == "Unresolved" for row in eligible_rows)
    metrics = {
        "Total": total,
        "Used": "Unknown" if unknown_usage else f"{used}/{total}",
        "Progress": f"{completed}/{eligible}",
        "Skipped": f"{skipped}/{total}",
        "Correct": f"{correct}/{eligible}",
        "Invalid": f"{invalid}/{eligible}",
        "Unresolved": f"{unresolved}/{eligible}",
        "Partial match": f"{sum(r['Status'] == 'Partial match' for r in eligible_rows)}/{eligible}",
        "Needs review": f"{sum(r['Status'] == 'Needs review' for r in eligible_rows)}/{eligible}",
    }
    metric_help = {
        "Total": "All references in the bibliography, including unused entries.",
        "Progress": "Completed checks of eligible entries / all eligible entries. "
        "Completed includes unresolved results; pending checks are excluded.",
        "Used": "References cited in the compiled AUX file / total references.",
        "Skipped": "Citations explicitly marked unused by the AUX file / total references. "
        "Unknown usage does not count as skipped.",
        "Correct": "Eligible references whose checked metadata matches authoritative evidence "
        "/ all eligible references.",
        "Invalid": "Eligible references with a confirmed metadata discrepancy "
        "/ all eligible references.",
        "Unresolved": "Eligible references with no record available to compare "
        "/ all eligible references.",
        "Partial match": "Eligible references with a matching abbreviated author list and "
        "otherwise "
        "matching checked fields / all eligible references.",
        "Needs review": "Records were found, but evidence is incomplete, ambiguous, or conflicting "
        "/ all eligible references.",
    }
    for column, (label, value) in zip(st.columns(len(metrics)), metrics.items(), strict=True):
        column.metric(
            label,
            value,
            help=metric_help[label],
        )
    usage_filter, error_filter = st.columns(2)
    hide_unused = usage_filter.toggle("Hide unused/skipped")
    errors_only = error_filter.toggle(
        "Show errors only",
        help="Show automated or agent Invalid/Unresolved results, plus failed source requests.",
    )
    visible_rows = []
    for row, item in zip(rows, report["items"], strict=True):
        if hide_unused and (row["Used in paper"] == "No" or row["Status"] == "Skipped"):
            continue
        failed_source = any(
            source.get("status") == "error"
            for source in item["validations"].get("correctness", {}).get("methods", [])
        )
        if (
            errors_only
            and row["Status"] not in {"Invalid", "Unresolved"}
            and row.get("Agent") not in {"Invalid", "Unresolved"}
            and not failed_source
        ):
            continue
        visible_rows.append(row)
    if not visible_rows:
        st.info("No references match these filters.")
        return
    event = st.dataframe(
        status_rows(visible_rows),
        hide_index=True,
        width="stretch",
        height="content",
        on_select="rerun",
        selection_mode="single-cell",
        key=f"references_{st.session_state.get('table_revision', 0)}_{hide_unused}_{errors_only}",
        column_config={
            "Status": status_column(),
            "Agent": status_column("Agent"),
            "Citation key": st.column_config.TextColumn(width="medium"),
            "Found": st.column_config.TextColumn(help="Found records / applicable sources"),
            "Consensus": st.column_config.TextColumn(help="Agreeing sources / found records"),
            "Note": st.column_config.TextColumn(width="large"),
        },
    )
    if event.selection.cells:
        index = event.selection.cells[0][0]
        st.query_params["key"] = visible_rows[index]["Citation key"]
        st.rerun()


def response_view(item, cache_dir):
    try:
        entries = cache_entries(cache_dir, item["entry"]["key"])
    except (OSError, ValueError, KeyError) as exc:
        st.info(f"Cached responses unavailable: {exc}")
        return
    if not entries:
        st.info("No raw cached responses for this reference.")
        return
    index = st.selectbox(
        "Response",
        range(len(entries)),
        format_func=lambda n: (
            f"{entries[n]['method']} · HTTP {entries[n]['status_code']} · "
            f"{entries[n]['retrieved_at']}"
        ),
    )
    entry = entries[index]
    code = entry["status_code"]
    st.badge(f"HTTP {code}", color="green" if 200 <= code < 300 else "red")
    try:
        _, text = read_response(cache_dir, entry)
    except (OSError, ValueError, LookupError) as exc:
        st.error(str(exc))
        return
    st.caption(f"{entry['path']} · SHA-256 verified")
    extension = Path(entry["path"]).suffix
    if extension == ".json":
        try:
            st.json(json.loads(text), expanded=2)
        except ValueError:
            st.code(text, language="text")
    elif extension == ".xml":
        try:
            st.code(pretty_xml(text), language="xml")
        except Exception:
            st.code(text, language="xml")
    else:
        # Raw HTML source is displayed verbatim rather than executing a cached page.
        st.code(text, language="html" if extension == ".html" else "text")


def detail(item, cache_dir):
    if st.button("← All references"):
        st.query_params.clear()
        st.session_state["table_revision"] = st.session_state.get("table_revision", 0) + 1
        st.rerun()
    summary = table_rows({"items": [item]})[0]
    status_area, sources_column = st.columns(2)
    status_area.caption("Automated status" if item.get("agent_review") else "Status")
    status_area.badge(
        summary["Status"],
        color=STATUS_COLORS[summary["Status"]],
        help="Unresolved means no record is available to compare. "
        "Partial match means the supplied author prefix matches; "
        "Needs review means other uncertainty. "
        "Pending means verification has not finished; Skipped means the citation is unused.",
    )
    sources_column.metric(
        "Resolved sources",
        summary["Found"],
        help="Sources that identified an unambiguous record / applicable sources checked so far. "
        "Sources that are not applicable are excluded; "
        "finding a record does not establish citation correctness.",
    )
    st.header(item["entry"]["key"])
    st.write(item["entry"].get("fields", {}).get("title", ""))
    authors = input_record(item["entry"]).get("authors", [])
    st.write(display(authors) if authors else "No authors listed.")
    result = item["validations"].get("correctness")
    methods = result.get("methods", []) if result else []
    review = item.get("agent_review")
    tabs = st.tabs(
        ["Comparison", "Cached responses", "Raw log"] + (["Agent evidence"] if review else [])
    )
    comparison, responses, raw_log = tabs[:3]
    if review:
        _agent_panel(tabs[3], review)
    _comparison_panel(comparison, item, review, summary, result, methods)
    with responses:
        response_view(item, cache_dir)
    with raw_log:
        if methods:
            st.json(methods, expanded=1)
        else:
            st.info("No source evidence available yet.")
        if review:
            st.json({"source": "agent", **review}, expanded=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="")
    parser.add_argument("--cache-dir", default=".bib-lint-cache")
    args, _ = parser.parse_known_args()
    st.set_page_config(page_title="Bib-Lint", layout="wide", initial_sidebar_state="collapsed")
    initial = args.report or ("references.json" if Path("references.json").exists() else "")
    st.session_state.setdefault("report_path", initial)
    workflow_controls()
    with st.sidebar:
        report_path = st.text_input("Report", key="report_path")
        is_workspace = bool(report_path) and Path(report_path).is_dir()
        cache_default = str(Path(report_path) / "cache") if is_workspace else args.cache_dir
        cache_dir = st.text_input(
            "Cache directory", value=cache_default, key=f"cache_{report_path}"
        )
        agent_default = (
            (Path(report_path) / "report.agent.json")
            if is_workspace
            else sidecar_path(report_path or "report.json")
        )
        agent_path = st.text_input(
            "Agent evidence", value=str(agent_default), key=f"agent_{report_path}"
        )
        st.button("Reload")
    if not report_path:
        st.title("Bib-Lint")
        st.info("Enter local paths above to start an audit, or open an existing audit directory.")
        return
    try:
        report = load_report(report_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Could not load report: {exc}")
        return
    try:
        for warning in attach_reviews(report, agent_path):
            st.warning(warning)
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        st.warning(f"Could not load agent evidence: {exc}")
    selected = st.query_params.get("key")
    if selected is None:
        overview(report)
        return
    item = next((i for i in report["items"] if i["entry"].get("key") == selected), None)
    if item is None:
        st.error("Citation key not found in this report.")
        if st.button("All references"):
            st.query_params.clear()
            st.rerun()
        return
    detail(item, cache_dir)


def _agent_panel(tab, review):
    with tab:
        st.badge(review["status"], color=STATUS_COLORS[review["status"]])
        st.write(review["summary"])
        st.caption(
            f"Reviewed {review['reviewed_at']} · Checked: "
            + ", ".join(review.get("checked_fields", []))
        )
        for evidence in review["evidence"]:
            st.link_button(evidence.get("title", "Primary evidence"), evidence["url"])
            if evidence["supports"] != review["summary"]:
                st.write(evidence["supports"])
        if review.get("limitations"):
            st.caption(review["limitations"])


def _comparison_panel(comparison, item, review, summary, result, methods):
    with comparison:
        if review and review["status"] != summary["Status"]:
            st.info(
                f"Agent assessment: {review['status']}; automated assessment: {summary['Status']}. "
                "See Agent evidence before applying automated suggestions."
            )
        st.subheader("Your entry")
        st.json(item["entry"], expanded=2)
        st.subheader("Suggested corrections")
        proposed = suggestions(item)
        if proposed:
            st.dataframe(proposed, hide_index=True, width="stretch")
            st.caption("Proposals only; the bibliography is not modified.")
        else:
            st.caption("No confirmed correction to propose from the available evidence.")
        st.subheader("Diff")
        if not result and not review:
            st.info("This reference has not been verified.")
        else:
            st.caption((result or {}).get("reason", ""))
            show_matches = st.toggle("Include matching fields")
            rows = comparison_rows(item, show_matches)
            if rows:
                st.table(
                    wrapped_status_rows(rows),
                    hide_index=True,
                    hide_header=False,
                    width="stretch",
                )
            else:
                st.info("No field differences available.")
            st.subheader("Resolved Sources")
            st.dataframe(
                source_rows(methods)
                + (
                    [
                        {
                            "Source": "agent",
                            "Status": [review["status"]],
                            "URL": review["evidence"][0]["url"],
                            "Error": "",
                            "Revision": "",
                            "Search scope": "",
                        }
                    ]
                    if review
                    else []
                ),
                hide_index=True,
                width="stretch",
                column_config={"URL": st.column_config.LinkColumn(), "Status": status_column()},
            )


if __name__ == "__main__":
    main()
