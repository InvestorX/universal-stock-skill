from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from universal_stock_skill.analysis.orchestrator import StockAnalysisDataBundle
from universal_stock_skill.data.canonical import CanonicalMetric


class PeerComparisonError(ValueError):
    pass


class PeerMetricRow(BaseModel):
    symbol: str = Field(min_length=1)
    requested_as_of: datetime
    market_observed_at: datetime
    market_cap: float | None = None
    price: float
    per: float | None = None
    pbr: float | None = None
    roe: float | None = None
    operating_margin: float | None = None
    free_cash_flow_yield: float | None = None
    revenue_yoy: float | None = None

    @model_validator(mode="after")
    def validate_timestamps(self) -> PeerMetricRow:
        for value in (self.requested_as_of, self.market_observed_at):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("peer timestamps must be timezone-aware")
        if self.market_observed_at > self.requested_as_of:
            raise ValueError("peer market_observed_at cannot exceed requested_as_of")
        return self


class PeerComparisonSet(BaseModel):
    subject_symbol: str = Field(min_length=1)
    requested_as_of: datetime
    rows: list[PeerMetricRow]

    def metric_values(self) -> dict[str, float | None]:
        result: dict[str, float | None] = {}
        metric_names = (
            "market_cap",
            "price",
            "per",
            "pbr",
            "roe",
            "operating_margin",
            "free_cash_flow_yield",
            "revenue_yoy",
        )
        for row in self.rows:
            for metric_name in metric_names:
                result[f"peer:{row.symbol}:{metric_name}"] = getattr(
                    row,
                    metric_name,
                )
        return result


def build_peer_comparison(
    subject: StockAnalysisDataBundle,
    peers: list[StockAnalysisDataBundle],
) -> PeerComparisonSet:
    expected_as_of = subject.requested_as_of
    all_bundles = [subject, *peers]

    symbols = [bundle.symbol.strip().upper() for bundle in all_bundles]
    if len(symbols) != len(set(symbols)):
        raise PeerComparisonError("peer symbols must be unique")

    for bundle in all_bundles:
        if bundle.requested_as_of != expected_as_of:
            raise PeerComparisonError(
                "all peer bundles must use the same requested_as_of"
            )

    return PeerComparisonSet(
        subject_symbol=subject.symbol.strip().upper(),
        requested_as_of=expected_as_of,
        rows=[_row(bundle) for bundle in all_bundles],
    )


def _row(bundle: StockAnalysisDataBundle) -> PeerMetricRow:
    revenue_trend = bundle.trends.get(CanonicalMetric.REVENUE)
    return PeerMetricRow(
        symbol=bundle.symbol.strip().upper(),
        requested_as_of=bundle.requested_as_of,
        market_observed_at=bundle.market.observed_at,
        market_cap=bundle.market.market_cap,
        price=bundle.market.price,
        per=bundle.metrics.per,
        pbr=bundle.metrics.pbr,
        roe=bundle.metrics.roe,
        operating_margin=bundle.metrics.operating_margin,
        free_cash_flow_yield=bundle.metrics.free_cash_flow_yield,
        revenue_yoy=(
            revenue_trend.year_over_year
            if revenue_trend is not None
            else None
        ),
    )
