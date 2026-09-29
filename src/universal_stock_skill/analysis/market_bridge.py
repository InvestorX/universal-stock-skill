from __future__ import annotations

from pydantic import BaseModel

from universal_stock_skill.analysis.bridge import SnapshotBridgeInputs
from universal_stock_skill.data.market import MarketSnapshot


class SnapshotDerivedInputs(BaseModel):
    average_equity: float
    capital_expenditure: float
    nopat: float | None = None
    average_invested_capital: float | None = None


class MissingMarketCapitalization(ValueError):
    pass


def build_snapshot_bridge_inputs(
    market: MarketSnapshot,
    derived: SnapshotDerivedInputs,
) -> SnapshotBridgeInputs:
    if market.market_cap is None:
        raise MissingMarketCapitalization(
            "market_cap is required; provide market_cap or shares_outstanding"
        )

    return SnapshotBridgeInputs(
        symbol=market.symbol,
        as_of=market.observed_at,
        price=market.price,
        market_cap=market.market_cap,
        average_equity=derived.average_equity,
        capital_expenditure=derived.capital_expenditure,
        nopat=derived.nopat,
        average_invested_capital=derived.average_invested_capital,
    )
