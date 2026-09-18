"""Bright Data Web Unlocker transport helpers."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

BRIGHTDATA_REQUEST_URL = "https://api.brightdata.com/request"

# Facebook intermittently returns a small generic error page with HTTP 200
# through Web Unlocker.  These equivalent logged-out entry points give the
# bootstrap a few independent chances to obtain a genuine LSD token.
BRIGHTDATA_BOOTSTRAP_URLS = (
    "https://www.facebook.com/?locale=en_US",
    "https://m.facebook.com/?locale=en_US",
    "https://mbasic.facebook.com/?locale=en_US",
)


@dataclass(frozen=True)
class BrightDataConfig:
    """Configuration for routing target requests through Web Unlocker."""

    api_key: str
    zone: str = "web_unlocker1"
    endpoint: str = BRIGHTDATA_REQUEST_URL

    @classmethod
    def from_values(
        cls,
        api_key: str | None = None,
        zone: str | None = None,
        endpoint: str | None = None,
    ) -> BrightDataConfig | None:
        key = api_key or os.environ.get("BRIGHTDATA_API_KEY")
        if not key:
            return None
        return cls(
            api_key=key,
            zone=zone or os.environ.get("BRIGHTDATA_ZONE", "web_unlocker1"),
            endpoint=endpoint or os.environ.get(
                "BRIGHTDATA_REQUEST_URL", BRIGHTDATA_REQUEST_URL
            ),
        )

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }


def build_brightdata_payload(
    config: BrightDataConfig,
    method: str,
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    data: Mapping[str, Any] | str | bytes | None = None,
    headers: Mapping[str, str] | None = None,
    session: str | None = None,
) -> dict[str, Any]:
    """Translate a target HTTP request into Bright Data's request envelope."""
    if params:
        parts = urlsplit(url)
        query = parse_qsl(parts.query, keep_blank_values=True)
        query.extend(parse_qsl(urlencode(params, doseq=True), keep_blank_values=True))
        url = urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    payload: dict[str, Any] = {
        "zone": config.zone,
        "url": url,
        "format": "raw",
        "method": method.upper(),
    }
    if session:
        payload["session"] = session
    if headers:
        payload["headers"] = dict(headers)
    if data is not None:
        if isinstance(data, Mapping):
            payload["body"] = urlencode(data, doseq=True)
        elif isinstance(data, bytes):
            payload["body"] = data.decode("utf-8")
        else:
            payload["body"] = data
    return payload
