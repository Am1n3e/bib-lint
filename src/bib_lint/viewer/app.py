"""Streamlit entry point. All UI uses built-in Streamlit components."""

import argparse
import json
from pathlib import Path

import streamlit as st

from bib_lint.viewer.data import (
    cache_entries,
    comparison_rows,
    load_report,
    pretty_xml,
    read_response,
    suggestions,
    table_rows,
)


def overview(report):
    st.title("Bib-Lint")
    rows = table_rows(report)
    total = len(rows)
    used_rows = [row for row in rows if row["Used in paper"] == "Yes"]
    used = len(used_rows)
    skipped = sum(row["Status"] == "Skipped" for row in rows)
    completed = sum(row["Status"] in {"Yes", "No", "Unresolved"} for row in rows)
    correct = sum(row["Status"] == "Yes" for row in used_rows)
    invalid = sum(row["Status"] == "No" for row in used_rows)
    unresolved = sum(row["Status"] == "Unresolved" for row in used_rows)
    metrics = {
        "Total": total,
        "Progress": f"{completed + skipped}/{total}",
        "Used": f"{used}/{total}",
        "Skipped": f"{skipped}/{total}",
        "Correct": f"{correct}/{used}",
        "Invalid": f"{invalid}/{used}",
        "Unresolved": f"{unresolved}/{used}",
    }
    for column, (label, value) in zip(st.columns(len(metrics)), metrics.items(), strict=True):
        column.metric(
            label,
            value,
            help="Completed checks plus skipped references / total references."
            if label == "Progress"
            else None,
        )
    event = st.dataframe(
        rows,
        hide_index=True,
        width="stretch",
        height="content",
        on_select="rerun",
        selection_mode="single-cell",
        key=f"references_{st.session_state.get('table_revision', 0)}",
        column_config={
            "Citation key": st.column_config.TextColumn(width="medium"),
            "Found": st.column_config.TextColumn(help="Found records / applicable methods"),
            "Consensus": st.column_config.TextColumn(help="Agreeing methods / found records"),
            "Note": st.column_config.TextColumn(width="large"),
        },
    )
    if event.selection.cells:
        index = event.selection.cells[0][0]
        st.query_params["key"] = report["items"][index]["entry"]["key"]
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
    st.title(item["entry"]["key"])
    st.write(item["entry"].get("fields", {}).get("title", ""))
    result = item["validations"].get("correctness")
    methods = result.get("methods", []) if result else []
    comparison, responses, raw_log = st.tabs(["Comparison", "Cached responses", "Raw log"])
    with comparison:
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
        if not result:
            st.info("This reference has not been verified.")
        else:
            st.caption(result.get("reason", ""))
            show_matches = st.toggle("Include matching fields")
            rows = comparison_rows(item, show_matches)
            if rows:
                st.dataframe(rows, hide_index=True, width="stretch")
            else:
                st.info("No field differences available.")
            st.dataframe(
                [
                    {
                        "Method": m["name"],
                        "Outcome": m["status"],
                        "URL": m.get("source_url") or (m.get("found_ref") or {}).get("url"),
                        "Error": m.get("error", {}).get("message", ""),
                    }
                    for m in methods
                ],
                hide_index=True,
                width="stretch",
                column_config={"URL": st.column_config.LinkColumn()},
            )
    with responses:
        response_view(item, cache_dir)
    with raw_log:
        if methods:
            st.json(methods, expanded=1)
        else:
            st.info("No method evidence available yet.")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", default="references.json")
    parser.add_argument("--cache-dir", default=".bib-lint-cache")
    args, _ = parser.parse_known_args()
    st.set_page_config(
        page_title="Bib-Lint", layout="wide", initial_sidebar_state="collapsed"
    )
    with st.sidebar:
        report_path = st.text_input("Report", value=args.report)
        cache_dir = st.text_input("Cache directory", value=args.cache_dir)
        st.button("Reload")
    try:
        report = load_report(report_path)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        st.error(f"Could not load report: {exc}")
        return
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


if __name__ == "__main__":
    main()
