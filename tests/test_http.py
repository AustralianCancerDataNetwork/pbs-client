from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse

import pytest

from pbs_client.config import PBSSettings
from pbs_client.errors import PBSTransportError
from pbs_client.http import GlobalRateLimiter, PBSClient, TransportResponse


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
        PBSSettings(subscription_key="test", base_url="https://example.test", rate_limit_seconds=0),
        transport=transport,
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

    PBSClient(transport=transport)
    assert called is False


def test_timeout_after_retries_is_actionable():
    def transport(*args):
        raise TimeoutError("read timed out")

    client = PBSClient(
        PBSSettings(subscription_key="test", rate_limit_seconds=0),
        transport=transport,
        sleeper=lambda _: None,
        max_retries=1,
    )

    with pytest.raises(PBSTransportError) as caught:
        client.fetch_page("/restrictions", limit=1000)

    assert caught.value.timed_out is True
    assert caught.value.attempts == 2
    assert "timed out after 2 attempts" in str(caught.value)
