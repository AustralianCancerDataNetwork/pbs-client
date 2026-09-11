from __future__ import annotations

import json
from io import BytesIO
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse

import pytest

from pbs_client.config import MIN_RATE_LIMIT_SECONDS, PBSSettings
from pbs_client.errors import PBSAPIError, PBSHTTPError, PBSTransportError
from pbs_client.http import DEFAULT_PAGE_SIZE, GlobalRateLimiter, PBSClient, TransportResponse


def test_pagination_and_headers_are_fixture_driven(fixture_dir):
    responses = {
        1: json.loads((fixture_dir / "schedules-page-1.json").read_text()),
        2: {
            "data": [{"schedule_code": 1002}],
            "_meta": {"page": 2, "count": 1, "total_records": 2},
            "_links": [],
        },
    }
    responses[1]["_meta"]["total_records"] = 2
    calls = []

    def transport(method, url, headers):
        query = parse_qs(urlparse(url).query)
        calls.append((method, query, headers))
        page = int(query["page"][0])
        return TransportResponse(200, {}, json.dumps(responses[page]).encode())

    GlobalRateLimiter.reset_for_tests()
    client = PBSClient(
        PBSSettings(
            subscription_key="test",
            base_url="https://example.test",
            rate_limit_seconds=MIN_RATE_LIMIT_SECONDS,
        ),
        transport=transport,
        limiter=GlobalRateLimiter(0),
    )
    pages = list(client.iter_pages("/schedules", limit=1))

    assert [page.page for page in pages] == [1, 2]
    assert pages[0].messages
    assert all("schedule_code" not in call[1] for call in calls)
    assert all(call[2]["Subscription-Key"] == "test" for call in calls)


def test_client_construction_does_not_make_network_call():
    called = False

    def transport(*args):
        nonlocal called
        called = True
        raise AssertionError("network call during construction")

    PBSClient(PBSSettings(subscription_key="test"), transport=transport)
    assert called is False


def test_default_page_size_is_conservative():
    calls = []

    def transport(method, url, headers):
        calls.append(url)
        return TransportResponse(200, {}, b'{"data": [], "_meta": {}, "_links": []}')

    client = PBSClient(
        PBSSettings(
            subscription_key="test",
            base_url="https://example.test",
            rate_limit_seconds=MIN_RATE_LIMIT_SECONDS,
        ),
        transport=transport,
        limiter=GlobalRateLimiter(0),
    )

    client.fetch_page("/restrictions")

    assert f"limit={DEFAULT_PAGE_SIZE}" in calls[0]


def test_invalid_json_reports_bounded_response_diagnostic():
    def transport(*args):
        return TransportResponse(
            200,
            {"Content-Type": "text/html"},
            b"<html>temporary upstream error</html>",
        )

    client = PBSClient(
        PBSSettings(subscription_key="test", rate_limit_seconds=MIN_RATE_LIMIT_SECONDS),
        transport=transport,
        limiter=GlobalRateLimiter(0),
    )

    with pytest.raises(PBSAPIError) as caught:
        client.fetch_page("/restrictions")

    message = str(caught.value)
    assert "HTTP 200" in message
    assert "content-type='text/html'" in message
    assert "body_bytes=37" in message
    assert "temporary upstream error" in message


def test_http_error_preserves_status_and_honours_retry_after():
    calls = 0
    sleeps = []

    def transport(*args):
        nonlocal calls
        calls += 1
        raise HTTPError(
            "https://example.test/restrictions?page=1",
            429,
            "too many requests",
            {"Retry-After": "7"},
            BytesIO(b"rate limited"),
        )

    client = PBSClient(
        PBSSettings(subscription_key="test", rate_limit_seconds=MIN_RATE_LIMIT_SECONDS),
        transport=transport,
        limiter=GlobalRateLimiter(0, sleeper=sleeps.append),
        max_retries=1,
        backoff_base=2,
    )

    with pytest.raises(PBSHTTPError) as caught:
        client.fetch_page("/restrictions")

    assert calls == 2
    assert caught.value.status_code == 429
    assert caught.value.attempts == 2
    assert caught.value.retryable is True
    assert caught.value.retry_after_seconds == 7
    assert sleeps == [7]


def test_rate_limit_cannot_be_configured_below_quota_floor():
    with pytest.raises(ValueError, match="at least 3 seconds"):
        PBSSettings(subscription_key="test", rate_limit_seconds=2)


def test_timeout_after_retries_is_actionable():
    def transport(*args):
        raise TimeoutError("read timed out")

    client = PBSClient(
        PBSSettings(subscription_key="test", rate_limit_seconds=MIN_RATE_LIMIT_SECONDS),
        transport=transport,
        limiter=GlobalRateLimiter(0),
        sleeper=lambda _: None,
        max_retries=1,
    )

    with pytest.raises(PBSTransportError) as caught:
        client.fetch_page("/restrictions", limit=1000)

    assert caught.value.timed_out is True
    assert caught.value.attempts == 2
    assert "timed out after 2 attempts" in str(caught.value)
