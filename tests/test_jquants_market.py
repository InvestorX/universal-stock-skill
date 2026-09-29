from __future__ import annotations

from datetime import UTC, datetime

import httpx
import pytest

from universal_stock_skill.data.jquants_market import (
    JQuantsConfig,
    JQuantsMarketDataError,
    JQuantsMarketDataSource,
)


def transport(
    bars: list[dict],
    valuation: list[dict],
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "test-key"
        assert request.url.params["code"] == "7203"

        if request.url.path.endswith("/equities/bars/daily"):
            return httpx.Response(200, json={"data": bars})
        if request.url.path.endswith("/equities/valuation"):
            return httpx.Response(200, json={"data": valuation})
        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_jquants_builds_market_snapshot_with_valuation_market_cap() -> None:
    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=transport(
            bars=[
                {"Date": "2026-09-28", "Code": "72030", "C": 2990, "AdjC": 2990},
                {"Date": "2026-09-29", "Code": "72030", "C": 3000, "AdjC": 3000},
            ],
            valuation=[
                {
                    "Date": "2026-09-29",
                    "Code": "72030",
                    "MktCap": 40_000_000,
                }
            ],
        ),
    )

    result = await source.get_market_snapshot(
        "7203",
        datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
    )

    assert result.symbol == "7203"
    assert result.price == 3000
    assert result.currency == "JPY"
    assert result.market_cap == 40_000_000_000_000
    assert result.source == "jquants:v2"
    await source.aclose()


@pytest.mark.asyncio
async def test_same_day_close_is_not_visible_before_tse_close() -> None:
    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=transport(
            bars=[
                {"Date": "2026-09-28", "Code": "72030", "C": 2900},
                {"Date": "2026-09-29", "Code": "72030", "C": 3000},
            ],
            valuation=[],
        ),
    )

    result = await source.get_market_snapshot(
        "7203",
        datetime(2026, 9, 29, 5, 0, tzinfo=UTC),
    )

    assert result.price == 2900
    assert result.observed_at.isoformat() == "2026-09-28T15:30:00+09:00"
    await source.aclose()


@pytest.mark.asyncio
async def test_market_cap_is_not_borrowed_from_a_different_date() -> None:
    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=transport(
            bars=[{"Date": "2026-09-29", "Code": "72030", "C": 3000}],
            valuation=[
                {
                    "Date": "2026-09-28",
                    "Code": "72030",
                    "MktCap": 39_000_000,
                }
            ],
        ),
    )

    result = await source.get_market_snapshot(
        "7203",
        datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
    )

    assert result.price == 3000
    assert result.market_cap is None
    await source.aclose()


@pytest.mark.asyncio
async def test_unadjusted_close_is_used_for_valuation_snapshot() -> None:
    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=transport(
            bars=[
                {
                    "Date": "2026-09-29",
                    "Code": "72030",
                    "C": 3000,
                    "AdjC": 1500,
                }
            ],
            valuation=[],
        ),
    )

    result = await source.get_market_snapshot(
        "7203",
        datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
    )

    assert result.price == 3000
    await source.aclose()


@pytest.mark.asyncio
async def test_pagination_is_followed() -> None:
    calls: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        key = request.url.params.get("pagination_key")
        calls.append(key)

        if request.url.path.endswith("/equities/bars/daily"):
            if key is None:
                return httpx.Response(
                    200,
                    json={
                        "data": [{"Date": "2026-09-28", "Code": "72030", "C": 2900}],
                        "pagination_key": "next",
                    },
                )
            return httpx.Response(
                200,
                json={"data": [{"Date": "2026-09-29", "Code": "72030", "C": 3000}]},
            )

        if request.url.path.endswith("/equities/valuation"):
            return httpx.Response(200, json={"data": []})

        return httpx.Response(404)

    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=httpx.MockTransport(handler),
    )

    result = await source.get_market_snapshot(
        "7203",
        datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
    )

    assert result.price == 3000
    assert "next" in calls
    await source.aclose()


@pytest.mark.asyncio
async def test_http_error_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "invalid api key"})

    source = JQuantsMarketDataSource(
        JQuantsConfig(api_key="test-key"),
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(JQuantsMarketDataError):
        await source.get_market_snapshot(
            "7203",
            datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
        )

    await source.aclose()


def test_config_can_load_api_key_from_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JQUANTS_API_KEY", "env-key")

    config = JQuantsConfig.from_env()

    assert config.api_key == "env-key"
    assert config.base_url == "https://api.jquants.com/v2"


def test_config_requires_environment_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("JQUANTS_API_KEY", raising=False)

    with pytest.raises(ValueError):
        JQuantsConfig.from_env()
