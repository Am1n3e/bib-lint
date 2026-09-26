"""One independent verification adapter per provider; common normalized records."""

import os
import re
import xml.etree.ElementTree as ET
from urllib.parse import quote, urljoin, urlsplit

from bs4 import BeautifulSoup

from bib_lint.verification.http import LookupFailure
from bib_lint.verification.matching import (
    arxiv_id,
    doi,
    identity_match,
    name_parts,
    plain,
    select_result,
)


def _query(record):
    return plain(record.get("title") or "")


def _first(values):
    return values[0] if values else None


def _crossref(record):
    year = None
    for key in ("published-print", "published-online", "published", "issued"):
        parts = record.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            year = parts[0][0]
            break
    return {
        "title": _first(record.get("title")),
        "authors": [
            {"given": a.get("given", ""), "family": a.get("family") or a.get("name", "")}
            for a in record.get("author", [])
        ],
        "year": year,
        "venue": _first(record.get("container-title")),
        "identifiers": {"doi": doi(record.get("DOI"))},
        "url": record.get("URL"),
    }


def _direct(client, url, transform, **kwargs):
    try:
        return transform(client.json(url, **kwargs))
    except LookupFailure as exc:
        if exc.code == "not_found":
            return None
        raise


def verify_reference_crossref(record, client):
    params = {}
    if os.environ.get("CROSSREF_MAILTO"):
        params["mailto"] = os.environ["CROSSREF_MAILTO"]
    identifier = record["identifiers"].get("doi")
    candidates = []
    if identifier:
        found = _direct(
            client,
            "https://api.crossref.org/works/" + quote(identifier, safe=""),
            lambda data: _crossref(data["message"]),
            params=params,
        )
        if found:
            candidates.append(found)
            if identity_match(record, found):
                return select_result("crossref", record, candidates, authority=True, lookup="doi")
    data = client.json(
        "https://api.crossref.org/works",
        params={**params, "query.bibliographic": _query(record), "rows": 5},
    )
    candidates.extend(_crossref(item) for item in data["message"]["items"])
    return select_result("crossref", record, candidates, authority=True)


def _openalex(record):
    location = record.get("primary_location") or {}
    source = location.get("source") or {}
    return {
        "title": record.get("title"),
        "authors": [name_parts(a["author"]["display_name"]) for a in record.get("authorships", [])],
        "year": record.get("publication_year"),
        "venue": source.get("display_name"),
        "identifiers": {"doi": doi(record.get("doi"))},
        "url": record.get("id"),
    }


def verify_reference_openalex(record, client):
    params = {}
    if os.environ.get("OPENALEX_API_KEY"):
        params["api_key"] = os.environ["OPENALEX_API_KEY"]
    candidates = []
    identifier = record["identifiers"].get("doi")
    if identifier:
        found = _direct(
            client,
            "https://api.openalex.org/works/https://doi.org/" + quote(identifier, safe=""),
            _openalex,
            params=params,
        )
        if found:
            candidates.append(found)
            if identity_match(record, found):
                return select_result("openalex", record, candidates, lookup="doi")
    data = client.json(
        "https://api.openalex.org/works", params={**params, "search": _query(record), "per_page": 5}
    )
    candidates.extend(_openalex(item) for item in data["results"])
    return select_result("openalex", record, candidates)


def _semantic(record):
    external = record.get("externalIds") or {}
    return {
        "title": record.get("title"),
        "authors": [name_parts(a["name"]) for a in record.get("authors", [])],
        "year": record.get("year"),
        "venue": record.get("venue"),
        "identifiers": {
            k: v
            for k, v in {"doi": doi(external.get("DOI")), "arxiv": external.get("ArXiv")}.items()
            if v
        },
        "url": record.get("url"),
    }


def verify_reference_semantic_scholar(record, client):
    headers = {}
    if os.environ.get("SEMANTIC_SCHOLAR_API_KEY"):
        headers["x-api-key"] = os.environ["SEMANTIC_SCHOLAR_API_KEY"]
    params = {"fields": "title,authors,year,venue,externalIds,url"}
    candidates = []
    identifiers = record["identifiers"]
    identifier = (
        "DOI:" + identifiers["doi"]
        if identifiers.get("doi")
        else "ARXIV:" + identifiers["arxiv"]
        if identifiers.get("arxiv")
        else None
    )
    if identifier:
        found = _direct(
            client,
            "https://api.semanticscholar.org/graph/v1/paper/" + quote(identifier, safe=""),
            _semantic,
            params=params,
            headers=headers,
        )
        if found:
            candidates.append(found)
            if identity_match(record, found):
                return select_result("semantic_scholar", record, candidates, lookup="identifier")
    data = client.json(
        "https://api.semanticscholar.org/graph/v1/paper/search",
        params={**params, "query": _query(record), "limit": 5},
        headers=headers,
    )
    candidates.extend(_semantic(item) for item in data.get("data", []))
    return select_result("semantic_scholar", record, candidates)


def _arxiv_records(text):
    ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    records = []
    for entry in ET.fromstring(text).findall("a:entry", ns):
        url = entry.findtext("a:id", namespaces=ns)
        identifier = arxiv_id(url)
        if not identifier:
            raise LookupFailure("invalid_response", "arXiv returned an error record")
        identifiers = {"arxiv": identifier}
        published_doi = entry.findtext("x:doi", namespaces=ns)
        if published_doi:
            identifiers["doi"] = doi(published_doi)
        records.append(
            {
                "title": entry.findtext("a:title", namespaces=ns),
                "authors": [
                    name_parts(a.findtext("a:name", namespaces=ns))
                    for a in entry.findall("a:author", ns)
                ],
                "year": (entry.findtext("a:published", default="", namespaces=ns))[:4],
                "venue": "arXiv",
                "identifiers": identifiers,
                "url": url,
                "version": identifier,
                "record_type": "preprint",
            }
        )
    return records


def verify_reference_arxiv(record, client):
    identifier = record["identifiers"].get("arxiv")
    if identifier:
        candidates = _arxiv_records(
            client.get("https://export.arxiv.org/api/query", params={"id_list": identifier})
        )
        if any(identity_match(record, found) for found in candidates):
            return select_result("arxiv", record, candidates, authority=True, lookup="arxiv_id")
    # The API uses its own query language; strip quotes and operator punctuation from titles.
    title = re.sub(r"[^\w\s-]", " ", _query(record))
    candidates = _arxiv_records(
        client.get(
            "https://export.arxiv.org/api/query",
            params={"search_query": f'ti:"{title}"', "max_results": 5},
        )
    )
    return select_result("arxiv", record, candidates, authority=True)


PUBLISHER_HOSTS = {
    "proceedings.mlr.press",
    "papers.nips.cc",
    "proceedings.neurips.cc",
    "aclanthology.org",
    "jmlr.org",
    "www.jmlr.org",
}


def verify_reference_publisher(record, client):
    url = record.get("input_url", "")
    parsed = urlsplit(url)
    if parsed.hostname not in PUBLISHER_HOSTS or parsed.scheme not in {"http", "https"}:
        return {
            "name": "publisher",
            "status": "not_applicable",
            "authority": True,
            "found_ref": None,
            "agrees_with_consensus": None,
            "differences": [],
            "reason": "No supported publisher landing-page URL in entry",
        }
    if parsed.port not in {None, 80, 443} or parsed.username or parsed.password:
        raise LookupFailure("unsupported_url", "Nonstandard publisher URL")
    url = parsed._replace(scheme="https").geturl()
    for _ in range(4):
        try:
            text = client.get(url, allowed_hosts=PUBLISHER_HOSTS)
            break
        except LookupFailure as exc:
            if exc.code != "redirect":
                raise
            url = urljoin(url, str(exc))
    else:
        raise LookupFailure("redirect_limit", "Too many publisher redirects")
    soup = BeautifulSoup(text, "html.parser")

    def values(name):
        return [m.get("content", "") for m in soup.find_all("meta", attrs={"name": name})]

    title = _first(values("citation_title"))
    if not title:
        return select_result("publisher", record, [], authority=True, lookup="url")
    date = _first(values("citation_publication_date") or values("citation_date")) or ""
    found = {
        "title": title,
        "authors": [name_parts(a) for a in values("citation_author")],
        "year": date[:4],
        "venue": _first(values("citation_conference_title") or values("citation_journal_title")),
        "identifiers": {"doi": doi(_first(values("citation_doi")))},
        "url": url,
    }
    return select_result("publisher", record, [found], authority=True, lookup="url")


METHODS = {
    "crossref": verify_reference_crossref,
    "arxiv": verify_reference_arxiv,
    "openalex": verify_reference_openalex,
    "semantic_scholar": verify_reference_semantic_scholar,
    "publisher": verify_reference_publisher,
}
