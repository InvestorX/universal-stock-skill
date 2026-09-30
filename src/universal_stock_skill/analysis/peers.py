from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from statistics import fmean, median

from pydantic import BaseModel, Field, model_validator

from universal_stock_skill.analysis.orchestrator import StockAnalysisDataBundle
from universal_stock_skill.data.canonical import CanonicalMetric


class PeerComparisonError(ValueError):
    pass


class PeerMetricOrder(StrEnum):
    ASCENDING = "ascending"
    DESCENDING = "descending"


PEER_POSITION_ORDERS: dict[str, PeerMetricOrder] = {
    "per": PeerMetricOrder.ASCENDING,
    "pbr": PeerMetricOrder.ASCENDING,
    "roe": PeerMetricOrder.DESCENDING,
    "operating_margin": PeerMetricOrder.DESCENDING,
    "free_cash_flow_yield": PeerMetricOrder.DESCENDING,
    "revenue_yoy": PeerMetricOrder.DESCENDING,
}


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
    notes: list[str] = Field(default_factory=list)

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


class PeerMetricPosition(BaseModel):
    metric: str = Field(min_length=1)
    order: PeerMetricOrder
    subject_value: float | None
    rank: int | None
    available_count: int = Field(ge=0)
    peer_available_count: int = Field(ge=0)
    comparison_median: float | None
    delta_to_median: float | None
    peer_mean: float | None
    delta_to_peer_mean: float | None


class PeerPositioningSet(BaseModel):
    subject_symbol: str = Field(min_length=1)
    positions: list[PeerMetricPosition]

    def metric_values(self) -> dict[str, float | None]:
        result: dict[str, float | None] = {}
        for position in self.positions:
            prefix = (
                f"peer:{self.subject_symbol}:position:"
                f"{position.metric}:"
            )
            result[f"{prefix}rank"] = (
                float(position.rank)
                if position.rank is not None
                else None
            )
            result[f"{prefix}available_count"] = float(
                position.available_count
            )
            result[f"{prefix}peer_available_count"] = float(
                position.peer_available_count
            )
            result[f"{prefix}comparison_median"] = position.comparison_median
            result[f"{prefix}delta_to_median"] = position.delta_to_median
            result[f"{prefix}peer_mean"] = position.peer_mean
            result[f"{prefix}delta_to_peer_mean"] = position.delta_to_peer_mean
        return result

    def get(self, metric: str) -> PeerMetricPosition | None:
        return next(
            (
                position
                for position in self.positions
                if position.metric == metric
            ),
            None,
        )


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


def build_peer_positioning(
    comparison: PeerComparisonSet,
) -> PeerPositioningSet:
    subject_symbol = comparison.subject_symbol.strip().upper()
    matching_subject_rows = [
        row
        for row in comparison.rows
        if row.symbol.strip().upper() == subject_symbol
    ]
    if len(matching_subject_rows) != 1:
        raise PeerComparisonError(
            "peer comparison must contain exactly one subject row"
        )

    symbols = [row.symbol.strip().upper() for row in comparison.rows]
    if len(symbols) != len(set(symbols)):
        raise PeerComparisonError("peer comparison row symbols must be unique")

    subject_row = matching_subject_rows[0]
    positions = [
        _metric_position(
            comparison.rows,
            subject_row,
            metric,
            order,
        )
        for metric, order in PEER_POSITION_ORDERS.items()
    ]
    return PeerPositioningSet(
        subject_symbol=subject_symbol,
        positions=positions,
    )


def _metric_position(
    rows: list[PeerMetricRow],
    subject_row: PeerMetricRow,
    metric: str,
    order: PeerMetricOrder,
) -> PeerMetricPosition:
    subject_value = getattr(subject_row, metric)
    available_values = [
        float(value)
        for row in rows
        if (value := getattr(row, metric)) is not None
    ]
    peer_values = [
        float(value)
        for row in rows
        if row is not subject_row
        and (value := getattr(row, metric)) is not None
    ]

    comparison_median = (
        float(median(available_values))
        if available_values
        else None
    )
    peer_mean = float(fmean(peer_values)) if peer_values else None

    rank = None
    if subject_value is not None and len(available_values) >= 2:
        subject_numeric = float(subject_value)
        if order == PeerMetricOrder.ASCENDING:
            rank = 1 + sum(
                value < subject_numeric
                for value in available_values
            )
        else:
            rank = 1 + sum(
                value > subject_numeric
                for value in available_values
            )

    return PeerMetricPosition(
        metric=metric,
        order=order,
        subject_value=subject_value,
        rank=rank,
        available_count=len(available_values),
        peer_available_count=len(peer_values),
        comparison_median=comparison_median,
        delta_to_median=(
            float(subject_value) - comparison_median
            if subject_value is not None
            and comparison_median is not None
            else None
        ),
        peer_mean=peer_mean,
        delta_to_peer_mean=(
            float(subject_value) - peer_mean
            if subject_value is not None and peer_mean is not None
            else None
        ),
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
