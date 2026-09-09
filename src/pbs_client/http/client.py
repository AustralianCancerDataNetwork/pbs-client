"""Rate-limited, paginating PBS API v3 client using the standard library."""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator, Mapping, Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin
from urllib.request import Request, urlopen

from pbs_client.config import PBSSettings
from pbs_client.errors import PBSAPIError, PBSTransportError

logger = logging.getLogger(__name__)


class Sleeper(Protocol):
    def __call__(self, seconds: float) -> None: ...


@dataclass(frozen=True, slots=True)
class TransportResponse:
    status_code: int
    headers: Mapping[str, str]
    body: bytes


Transport = Callable[[str, str, Mapping[str, str]], TransportResponse]


def _urlopen_transport(method: str, url: str, headers: Mapping[str, str]) -> TransportResponse:
    request = Request(url, method=method, headers=dict(headers))
    with urlopen(request, timeout=60) as response:  # noqa: S310 - configured public API URL
        return TransportResponse(response.status, dict(response.headers), response.read())


class GlobalRateLimiter:
    """One process-wide monotonic gate shared by every PBS client instance."""

    _lock = threading.Lock()
    _next_allowed = 0.0

    def __init__(self, interval: float = 20.0, sleeper: Sleeper = time.sleep) -> None:
        self.interval = max(0.0, interval)
        self.sleeper = sleeper

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = max(0.0, self._next_allowed - now)
            if delay:
                self.sleeper(delay)
                now = time.monotonic()
            self.__class__._next_allowed = now + self.interval

    @classmethod
    def reset_for_tests(cls) -> None:
        with cls._lock:
            cls._next_allowed = 0.0


@dataclass(frozen=True, slots=True)
class Page:
    """One decoded API page, retaining pagination metadata and notices."""

    endpoint: str
    page: int
    limit: int
    records: list[dict[str, Any]]
    metadata: dict[str, Any] = field(default_factory=dict)
    links: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_records(self) -> int | None:
        value = self.metadata.get("total_records")
        return int(value) if value is not None else None

    @property
    def has_next(self) -> bool:
        return any(str(link.get("rel", "")).lower() == "next" for link in self.links)

    @property
    def messages(self) -> list[Any]:
        info = self.metadata.get("info", {})
        if isinstance(info, Mapping):
            messages = info.get("messages", [])
            return messages if isinstance(messages, list) else [messages]
        return []


class PBSClient:
    """Explicit HTTP client for the public PBS API.

    Construction is side-effect free.  Requests happen only through
    :meth:`fetch_page` or :meth:`iter_pages`, and every attempt passes through
    the shared rate limiter, including retries and pagination.
    """

    def __init__(
        self,
        settings: PBSSettings | None = None,
        *,
        transport: Transport = _urlopen_transport,
        limiter: GlobalRateLimiter | None = None,
        sleeper: Sleeper = time.sleep,
        max_retries: int = 3,
        backoff_base: float = 2.0,
    ) -> None:
        self.settings = settings or PBSSettings.from_env()
        self.transport = transport
        self.limiter = limiter or GlobalRateLimiter(self.settings.rate_limit_seconds, sleeper)
        self.max_retries = max(0, max_retries)
        self.backoff_base = max(0.0, backoff_base)

    def fetch_page(
        self,
        endpoint: str,
        *,
        page: int = 1,
        limit: int = 100_000,
        params: Mapping[str, Any] | None = None,
    ) -> Page:
        """Fetch and decode one page without adding a schedule filter."""

        query: dict[str, Any] = dict(params or {})
        query.update(page=page, limit=limit)
        query_string = urlencode(query, doseq=True)
        url = urljoin(self.settings.base_url.rstrip("/") + "/", endpoint.lstrip("/"))
        if query_string:
            url = f"{url}?{query_string}"
        response = self._request(url)
        try:
            document = json.loads(response.body.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise PBSAPIError(f"PBS endpoint {endpoint} returned invalid JSON") from exc
        if not isinstance(document, dict) or not isinstance(document.get("data"), list):
            raise PBSAPIError(f"PBS endpoint {endpoint} returned no JSON data array")
        metadata = document.get("_meta", {})
        links = document.get("_links", [])
        if isinstance(links, dict):
            links = [links]
        if not isinstance(metadata, dict) or not isinstance(links, list):
            raise PBSAPIError(f"PBS endpoint {endpoint} returned malformed pagination metadata")
        return Page(endpoint, page, limit, document["data"], metadata, links)

    def iter_pages(
        self,
        endpoint: str,
        *,
        limit: int = 100_000,
        params: Mapping[str, Any] | None = None,
        start_page: int = 1,
    ) -> Iterator[Page]:
        """Yield sequential pages until the API says the collection is done."""

        page_number = max(1, start_page)
        while True:
            page = self.fetch_page(endpoint, page=page_number, limit=limit, params=params)
            yield page
            if not page.records or (len(page.records) < limit and not page.has_next):
                return
            if not page.has_next and page.total_records is not None:
                if page_number * limit >= page.total_records:
                    return
            if not page.has_next and page.total_records is None:
                return
            page_number += 1

    def iter_records(self, endpoint: str, **kwargs: Any) -> Iterator[dict[str, Any]]:
        """Yield records from all pages of an endpoint."""

        for page in self.iter_pages(endpoint, **kwargs):
            yield from page.records

    def _request(self, url: str) -> TransportResponse:
        headers = {
            "Subscription-Key": self.settings.subscription_key,
            "Accept": "application/json",
        }
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.limiter.acquire()
            try:
                response = self.transport("GET", url, headers)
                if response.status_code == 429 or response.status_code >= 500:
                    raise _RetryableStatus(response.status_code)
                if response.status_code >= 400:
                    raise PBSAPIError(f"PBS API returned HTTP {response.status_code} for {url}")
                return response
            except _RetryableStatus as exc:
                last_error = exc
                if attempt < self.max_retries:
                    logger.debug("PBS API returned HTTP %s; retrying", exc.status_code)
                else:
                    logger.warning(
                        "PBS API request exhausted retries with HTTP %s", exc.status_code
                    )
            except HTTPError as exc:
                if exc.code < 500 and exc.code != 429:
                    raise PBSAPIError(f"PBS API returned HTTP {exc.code} for {url}") from exc
                last_error = exc
            except (URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt < self.max_retries:
                    logger.debug("Transient PBS API transport error; retrying: %s", exc)
                else:
                    logger.warning("PBS API request exhausted transport retries: %s", exc)
            if attempt < self.max_retries:
                self.limiter.sleeper(self.backoff_base * (2**attempt))
        if last_error is not None:
            raise PBSTransportError(url, self.max_retries + 1, last_error) from last_error
        raise PBSAPIError(f"PBS API request failed after retries: {url}")


@dataclass(frozen=True, slots=True)
class _RetryableStatus(Exception):
    status_code: int
