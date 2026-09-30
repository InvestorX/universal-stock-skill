from datetime import UTC, datetime

import pytest

from universal_stock_skill.data.market import MarketSnapshot
from universal_stock_skill.data.market_selection import (
    MarketSnapshotSelectionError,
    select_market_snapshot,
)


def snapshot(
    observed_at: datetime,
    *,
    price: float,
    market_cap: float | None = None,
    source: str = "fixture",
) -> MarketSnapshot:
    return MarketSnapshot(
        symbol="7203",
        observed_at=observed_at,
        price=price,
        currency="JPY",
        source=source,
        market_cap=market_cap,
    )


def test_selects_latest_snapshot_not_after_as_of() -> None:
    result = select_market_snapshot(
        [
            snapshot(datetime(2026, 9, 28, 6, 0, tzinfo=UTC), price=2900),
            snapshot(datetime(2026, 9, 29, 6, 0, tzinfo=UTC), price=3000),
            snapshot(datetime(2026, 9, 30, 6, 0, tzinfo=UTC), price=3100),
        ],
        symbol="7203",
        as_of=datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
    )

    assert result.price == 3000


def test_future_only_snapshot_is_rejected() -> None:
    with pytest.raises(MarketSnapshotSelectionError):
        select_market_snapshot(
            [
                snapshot(
                    datetime(2026, 9, 30, 6, 0, tzinfo=UTC),
                    price=3100,
                )
            ],
            symbol="7203",
            as_of=datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
        )


def test_market_cap_can_be_required() -> None:
    result = select_market_snapshot(
        [
            snapshot(
                datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
                price=3000,
            ),
            snapshot(
                datetime(2026, 9, 28, 6, 0, tzinfo=UTC),
                price=2900,
                market_cap=39_000_000_000_000,
            ),
        ],
        symbol="7203",
        as_of=datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
        require_market_cap=True,
    )

    assert result.price == 2900
    assert result.market_cap == 39_000_000_000_000


def test_symbol_mismatch_is_rejected() -> None:
    with pytest.raises(MarketSnapshotSelectionError):
        select_market_snapshot(
            [
                MarketSnapshot(
                    symbol="6758",
                    observed_at=datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
                    price=12000,
                    currency="JPY",
                    source="fixture",
                )
            ],
            symbol="7203",
            as_of=datetime(2026, 9, 29, 7, 0, tzinfo=UTC),
        )
