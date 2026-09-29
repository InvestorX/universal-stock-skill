from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis.market_bridge import (
    MissingMarketCapitalization,
    SnapshotDerivedInputs,
    build_snapshot_bridge_inputs,
)
from universal_stock_skill.data.market import MarketSnapshot


def test_market_snapshot_derives_market_cap_from_shares() -> None:
    snapshot = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
        price=3000,
        currency="JPY",
        source="fixture",
        shares_outstanding=10_000_000_000,
    )

    assert snapshot.market_cap == 30_000_000_000_000
    assert snapshot.has_market_cap


def test_explicit_market_cap_is_preserved() -> None:
    snapshot = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
        price=3000,
        currency="JPY",
        source="fixture",
        market_cap=40_000_000_000_000,
        shares_outstanding=10_000_000_000,
    )

    assert snapshot.market_cap == 40_000_000_000_000


def test_market_snapshot_requires_timezone() -> None:
    with pytest.raises(ValueError):
        MarketSnapshot(
            symbol="7203",
            observed_at=datetime(2026, 9, 29, 6, 0),
            price=3000,
            currency="JPY",
            source="fixture",
        )


def test_market_bridge_builds_snapshot_inputs() -> None:
    market = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
        price=3000,
        currency="JPY",
        source="fixture",
        market_cap=40_000_000_000_000,
    )
    inputs = build_snapshot_bridge_inputs(
        market,
        SnapshotDerivedInputs(
            average_equity=30_000_000_000_000,
            capital_expenditure=4_000_000_000_000,
        ),
    )

    assert inputs.symbol == "7203"
    assert inputs.price == 3000
    assert inputs.market_cap == 40_000_000_000_000


def test_market_bridge_rejects_missing_market_cap() -> None:
    market = MarketSnapshot(
        symbol="7203",
        observed_at=datetime(2026, 9, 29, 6, 0, tzinfo=UTC),
        price=3000,
        currency="JPY",
        source="fixture",
    )

    with pytest.raises(MissingMarketCapitalization):
        build_snapshot_bridge_inputs(
            market,
            SnapshotDerivedInputs(
                average_equity=30_000_000_000_000,
                capital_expenditure=4_000_000_000_000,
            ),
        )
