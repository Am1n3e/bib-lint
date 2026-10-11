"""Bounded HTTP requests with per-provider pacing and reusable response evidence."""

import hashlib
import json
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx
from bs4 import BeautifulSoup

from bib_lint.verification.cache import ResponseCache


class LookupFailure(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def _http_error_message(response):
    """Return bounded, readable server details without echoed API credentials."""
    body = response.text
    if "html" in response.headers.get("content-type", "") or body.lstrip().startswith("<"):
        soup = BeautifulSoup(body, "html.parser")
        for element in soup(["script", "style"]):
            element.decompose()
        body = soup.get_text(" ", strip=True)
    request = response.request
    secrets = [request.url.params.get("api_key"), request.headers.get("x-api-key")]
    authorization = request.headers.get("authorization")
    if authorization:
        secrets.extend([authorization, authorization.removeprefix("Bearer ")])
    for secret in secrets:
        if secret:
            body = body.replace(secret, "[redacted]")
    body = re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", body)
    body = " ".join(re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", body).split())
    if len(body) > 500:
        body = body[:500] + "…"
    detail = response.reason_phrase or "HTTP request failed"
    if body and body.casefold() != detail.casefold():
        detail += f" — {body}"
    return f"HTTP {response.status_code}: {detail}"


class MetadataClient:
    def __init__(
        self, cache_dir: Path, *, refresh=False, timeout=20, transport=None, verbose=False
    ):
        self.cache_dir = Path(cache_dir)
        self.cache = ResponseCache(self.cache_dir)
        self.citation_key = "_unscoped"
        self.method = None
        self.refresh = refresh
        self.verbose = verbose
        self.client = httpx.Client(
            timeout=timeout,
            transport=transport,
            follow_redirects=False,
            headers={"User-Agent": "bib-lint/0.1 (reference verification)"},
        )
        self.last_request = {}
        self.evidence = []
        self.progress = None

    def emit(self, message):
        if self.progress:
            self.progress(message)

    def close(self):
        self.client.close()

    def dump_response(
        self,
        request,
        *,
        body=None,
        status=None,
        headers=None,
        reason=None,
        cached=False,
        attempt=None,
        error=None,
    ):
        if not self.verbose:
            return
        try:
            payload = json.loads(body) if body is not None else None
        except ValueError:
            payload = body
        event = {
            "url": str(request.url.copy_remove_param("api_key")),
            "cached": cached,
            "attempt": attempt,
            "status_code": status,
            "reason": reason,
            "headers": headers,
            "body": payload,
        }
        if error is not None:
            event["error"] = error
        secrets = [request.url.params.get("api_key"), request.headers.get("x-api-key")]
        authorization = request.headers.get("authorization")
        if authorization:
            secrets.extend([authorization, authorization.removeprefix("Bearer ")])

        def redact(value):
            if isinstance(value, dict):
                return {
                    key: "[redacted]"
                    if key.lower()
                    in {"authorization", "api_key", "x-api-key", "set-cookie", "cookie"}
                    else redact(item)
                    for key, item in value.items()
                }
            if isinstance(value, list):
                return [redact(item) for item in value]
            if isinstance(value, str):
                for secret in secrets:
                    if secret:
                        value = value.replace(secret, "[redacted]").replace(
                            quote(secret, safe=""), "[redacted]"
                        )
            return value

        content_type = (headers or {}).get("content-type", "").lower()
        is_markup = isinstance(body, str) and (
            "html" in content_type or "xml" in content_type or body.lstrip().startswith("<")
        )
        if is_markup:
            safe = redact(event)
            lines = [
                f"Response: HTTP {status} {reason or ''}".rstrip(),
                f"URL: {safe['url']}",
                f"Cached: {cached}; attempt: {attempt}",
            ]
            lines.extend(f"{key}: {value}" for key, value in (safe["headers"] or {}).items())
            self.emit("\n".join(lines) + "\n\n" + redact(body))
        else:
            self.emit("Response:\n" + json.dumps(redact(event), ensure_ascii=False, indent=2))

    def get(self, url, *, params=None, headers=None, allowed_hosts=None):
        host = urlsplit(url).hostname
        if allowed_hosts is not None and host not in allowed_hosts:
            raise LookupFailure("unsupported_host", "Redirect or URL is outside supported sites")
        request = self.client.build_request("GET", url, params=params, headers=headers)
        # Credentials affect neither the public record identity nor the persisted evidence.
        public_url = str(request.url.copy_remove_param("api_key"))
        key = hashlib.sha256(public_url.encode()).hexdigest()
        method = self.method or host or "unknown"
        saved = None if self.refresh else self.cache.load(self.citation_key, method, key)
        if saved is not None:
            raw, metadata = saved
            body = raw.decode(metadata.get("encoding", "utf-8"), errors="replace")
            self.evidence.append(
                {
                    "url": public_url,
                    "retrieved_at": metadata["retrieved_at"],
                    "cached": True,
                    "cache_key": key,
                    "cache_file": metadata["path"],
                    "sha256": metadata["sha256"],
                }
            )
            self.emit("Using checksum-verified cached response")
            self.dump_response(
                request,
                body=body,
                status=200,
                cached=True,
                reason=metadata.get("reason"),
                headers=metadata.get("headers"),
            )
            return body
        evidence = {
            "url": public_url,
            "requested_at": datetime.now(UTC).isoformat(),
            "cached": False,
            "attempts": 0,
        }
        self.evidence.append(evidence)
        interval = 3.1 if host == "export.arxiv.org" else 1.0
        semantic_scholar = host == "api.semanticscholar.org"
        backoffs = (10, 15, 20, 25, 30) if semantic_scholar else (2, 4)
        max_delay = 30 if semantic_scholar else 10
        for attempt in range(len(backoffs) + 1):
            delay = interval - (time.monotonic() - self.last_request.get(host, 0))
            if delay > 0:
                time.sleep(delay)
            self.last_request[host] = time.monotonic()
            evidence["attempts"] += 1
            try:
                response = self.client.send(request)
            except httpx.RequestError as exc:
                self.dump_response(
                    request,
                    attempt=attempt + 1,
                    error={"type": type(exc).__name__, "message": str(exc)},
                )
                if attempt < len(backoffs):
                    delay = backoffs[attempt]
                    self.emit(f"Network error backoff {delay:g} seconds")
                    time.sleep(delay)
                    continue
                raise LookupFailure("network_error", type(exc).__name__) from exc
            metadata = self.cache.save(self.citation_key, method, key, public_url, response)
            evidence.setdefault("responses", []).append(
                {
                    "cache_file": metadata["path"],
                    "sha256": metadata["sha256"],
                    "status_code": response.status_code,
                }
            )
            self.dump_response(
                request,
                body=response.text,
                status=response.status_code,
                reason=response.reason_phrase,
                headers=dict(response.headers),
                attempt=attempt + 1,
            )
            evidence["http_status"] = response.status_code
            if response.status_code in {429, 500, 502, 503, 504} and attempt < len(backoffs):
                retry = response.headers.get("Retry-After", str(backoffs[attempt]))
                try:
                    delay = float(retry)
                except ValueError:
                    delay = backoffs[attempt]
                if semantic_scholar:
                    delay = max(backoffs[attempt], delay)
                if delay > max_delay:
                    self.emit(f"Retry-After {delay:g} seconds exceeds retry budget; stopping")
                    break
                label = "Rate limit" if response.status_code == 429 else "Server error"
                self.emit(f"{label} backoff {max(0, delay):g} seconds")
                time.sleep(max(0, delay))
                continue
            break
        if response.status_code == 404:
            raise LookupFailure("not_found", _http_error_message(response))
        if response.status_code == 429:
            raise LookupFailure(
                "rate_limited", "Provider rate limit reached; " + _http_error_message(response)
            )
        if response.status_code in {401, 403}:
            raise LookupFailure("access_denied", _http_error_message(response))
        if 300 <= response.status_code < 400:
            raise LookupFailure("redirect", response.headers.get("Location", ""))
        if response.status_code != 200:
            raise LookupFailure("http_error", _http_error_message(response))
        evidence.update(
            retrieved_at=metadata["retrieved_at"],
            cache_key=key,
            cache_file=metadata["path"],
            sha256=metadata["sha256"],
        )
        return response.text

    def json(self, url, **kwargs):
        try:
            return json.loads(self.get(url, **kwargs))
        except json.JSONDecodeError as exc:
            raise LookupFailure("invalid_response", "Provider did not return valid JSON") from exc
