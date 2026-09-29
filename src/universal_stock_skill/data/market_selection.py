from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from universal_stock_skill.data.market import MarketSnapshot


class MarketSnapshotSelectionError(ValueError):
    pass


def select_market_snapshot(
    snapshots: Iterable[MarketSnapshot],
    *,
    symbol: str,
    as_of: datetime,
    require_market_cap: bool = False,
) -> MarketSnapshot:
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        raise ValueError("as_of must be timezone-aware")

    normalized_symbol = symbol.strip().upper()
    candidates = [
        snapshot
        for snapshot in snapshots
        if snapshot.symbol.strip().upper() == normalized_symbol
        and snapshot.observed_at <= as_of
        and (snapshot.market_cap is not None or not require_market_cap)
    ]

    if not candidates:
        requirement = " with market capitalization" if require_market_cap else ""
        raise MarketSnapshotSelectionError(
            f"no market snapshot{requirement} for {normalized_symbol} "
            f"at or before {as_of.isoformat()}"
        )

    return max(
        candidates,
        key=lambda snapshot: (
            snapshot.observed_at,
            snapshot.source,
        ),
    )
