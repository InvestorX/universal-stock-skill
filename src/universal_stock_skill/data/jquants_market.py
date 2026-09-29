from __future__ import annotations

from datetime import date, datetime, time, timedelta
from os import environ
from typing import Any, Self
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field

from universal_stock_skill.data.market import MarketSnapshot

JST = ZoneInfo("Asia/Tokyo")
TSE_CLOSE = time(15, 30)


class JQuantsConfig(BaseModel):
    api_key: str = Field(min_length=1)
    base_url: str = "https://api.jquants.com/v2"
    lookback_days: int = Field(default=14, ge=1, le=60)
    timeout_seconds: float = Field(default=30.0, gt=0)

    @classmethod
    def from_env(cls) -> Self:
        api_key = environ.get("JQUANTS_API_KEY")
        if not api_key:
            raise ValueError("JQUANTS_API_KEY is required")
        return cls(api_key=api_key)


class JQuantsMarketDataError(ValueError):
    pass


class JQuantsMarketDataSource:
    def __init__(
        self,
        config: JQuantsConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._config = config
        self._client = httpx.AsyncClient(
            base_url=config.base_url.rstrip("/"),
            headers={"x-api-key": config.api_key},
            timeout=config.timeout_seconds,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get_market_snapshot(
        self,
        symbol: str,
        as_of: datetime,
    ) -> MarketSnapshot:
        _require_aware(as_of)
        code = _normalize_code(symbol)
        end_date = as_of.astimezone(JST).date()
        start_date = end_date - timedelta(days=self._config.lookback_days)

        params = {
            "code": code,
            "from": start_date.isoformat(),
            "to": end_date.isoformat(),
        }
        bars = await self._get_all("/equities/bars/daily", params)
        valuation = await self._get_all("/equities/valuation", params)

        bar = _select_latest_bar(bars, as_of=as_of)
        if bar is None:
            raise JQuantsMarketDataError(
                f"no J-Quants daily close for {code} at or before {as_of.isoformat()}"
            )

        trading_date = _parse_date(bar)
        close = _read_number(bar, "C", "Close")
        if close is None or close <= 0:
            raise JQuantsMarketDataError(
                f"J-Quants daily bar has no usable close for {code} on {trading_date}"
            )

        valuation_row = _select_valuation_for_date(
            valuation,
            code=code,
            trading_date=trading_date,
        )
        market_cap = None
        if valuation_row is not None:
            market_cap_million_yen = _read_number(valuation_row, "MktCap")
            if market_cap_million_yen is not None and market_cap_million_yen > 0:
                market_cap = market_cap_million_yen * 1_000_000

        observed_at = datetime.combine(
            trading_date,
            TSE_CLOSE,
            tzinfo=JST,
        )

        return MarketSnapshot(
            symbol=_display_symbol(symbol),
            observed_at=observed_at,
            price=close,
            currency="JPY",
            source="jquants:v2",
            market_cap=market_cap,
        )

    async def get_price(self, symbol: str, as_of: datetime) -> float:
        snapshot = await self.get_market_snapshot(symbol, as_of)
        return snapshot.price

    async def _get_all(
        self,
        path: str,
        params: dict[str, str],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        pagination_key: str | None = None

        while True:
            query = dict(params)
            if pagination_key:
                query["pagination_key"] = pagination_key

            response = await self._client.get(path, params=query)
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise JQuantsMarketDataError(
                    f"J-Quants request failed: {response.status_code} {path}"
                ) from exc

            payload = response.json()
            rows.extend(_extract_rows(payload))

            pagination_key = payload.get("pagination_key")
            if not pagination_key:
                break

        return rows


def _require_aware(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")


def _normalize_code(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if len(normalized) in {4, 5} and normalized.isalnum():
        return normalized
    raise ValueError("J-Quants security code must be 4 or 5 alphanumeric characters")


def _display_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if len(normalized) == 5 and normalized.endswith("0"):
        return normalized[:4]
    return normalized


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        raise JQuantsMarketDataError("J-Quants response must be a JSON object")

    for key in ("data", "daily_quotes", "valuation"):
        value = payload.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]

    return []


def _select_latest_bar(
    rows: list[dict[str, Any]],
    *,
    as_of: datetime,
) -> dict[str, Any] | None:
    eligible: list[tuple[datetime, dict[str, Any]]] = []

    for row in rows:
        try:
            trading_date = _parse_date(row)
        except (KeyError, ValueError):
            continue

        observed_at = datetime.combine(
            trading_date,
            TSE_CLOSE,
            tzinfo=JST,
        )
        if observed_at <= as_of.astimezone(JST):
            eligible.append((observed_at, row))

    if not eligible:
        return None

    eligible.sort(key=lambda item: item[0], reverse=True)
    return eligible[0][1]


def _select_valuation_for_date(
    rows: list[dict[str, Any]],
    *,
    code: str,
    trading_date: date,
) -> dict[str, Any] | None:
    for row in rows:
        try:
            row_date = _parse_date(row)
        except (KeyError, ValueError):
            continue

        row_code = str(row.get("Code", "")).strip().upper()
        if row_date == trading_date and _codes_match(row_code, code):
            return row

    return None


def _codes_match(left: str, right: str) -> bool:
    if left == right:
        return True
    return left.rstrip("0") == right.rstrip("0")


def _parse_date(row: dict[str, Any]) -> date:
    return date.fromisoformat(str(row["Date"]))


def _read_number(row: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        raw = row.get(key)
        if raw is None or raw == "":
            continue
        try:
            return float(raw)
        except (TypeError, ValueError):
            continue
    return None
