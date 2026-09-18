from unittest.mock import AsyncMock, MagicMock

import pytest

from meta_ads_collector.async_client import AsyncMetaAdsClient
from meta_ads_collector.brightdata import BrightDataConfig, build_brightdata_payload
from meta_ads_collector.client import MetaAdsClient


def test_build_payload_preserves_target_request():
    config = BrightDataConfig("secret", "web_unlocker1")
    payload = build_brightdata_payload(
        config,
        "POST",
        "https://example.com/graphql?existing=1",
        params={"page": 2},
        data={"query": "shoes", "ids": ["1", "2"]},
        headers={"x-test": "yes"},
        session="session-id",
    )

    assert payload == {
        "zone": "web_unlocker1",
        "url": "https://example.com/graphql?existing=1&page=2",
        "format": "raw",
        "method": "POST",
        "session": "session-id",
        "headers": {"x-test": "yes"},
        "body": "query=shoes&ids=1&ids=2",
    }


def test_config_reads_environment_when_constructed(monkeypatch):
    monkeypatch.setenv("BRIGHTDATA_API_KEY", "environment-key")
    monkeypatch.setenv("BRIGHTDATA_ZONE", "environment-zone")

    config = BrightDataConfig.from_values()

    assert config is not None
    assert config.api_key == "environment-key"
    assert config.zone == "environment-zone"


def test_sync_client_routes_request_through_brightdata(monkeypatch):
    monkeypatch.delenv("BRIGHTDATA_API_KEY", raising=False)
    client = MetaAdsClient(brightdata_api_key="secret", max_retries=1)
    response = MagicMock(status_code=200)
    client.session.post = MagicMock(return_value=response)

    result = client._make_request("GET", "https://example.com", params={"q": "x"})

    assert result is response
    _, kwargs = client.session.post.call_args
    assert client.session.post.call_args.args[0] == "https://api.brightdata.com/request"
    assert kwargs["headers"]["Authorization"] == "Bearer secret"
    assert kwargs["json"]["url"] == "https://example.com?q=x"


@pytest.mark.asyncio
async def test_async_client_routes_request_through_brightdata(monkeypatch):
    monkeypatch.delenv("BRIGHTDATA_API_KEY", raising=False)
    client = AsyncMetaAdsClient(brightdata_api_key="secret", max_retries=1)
    response = MagicMock(status_code=200)
    client._client.post = AsyncMock(return_value=response)

    result = await client._make_request("POST", "https://example.com", data={"a": "b"})

    assert result is response
    _, kwargs = client._client.post.call_args
    assert client._client.post.call_args.args[0] == "https://api.brightdata.com/request"
    assert kwargs["json"]["method"] == "POST"
    assert kwargs["json"]["body"] == "a=b"
