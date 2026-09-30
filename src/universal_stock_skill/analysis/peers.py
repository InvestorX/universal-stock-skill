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


class PeerProfileAxis(StrEnum):
    PROFITABILITY = "profitability"
    GROWTH = "growth"
    VALUATION = "valuation"
    CASH_GENERATION = "cash_generation"


class PeerProfileBand(StrEnum):
    FIRST_THIRD = "first_third"
    MIDDLE_THIRD = "middle_third"
    LAST_THIRD = "last_third"
    UNRANKED = "unranked"


PEER_POSITION_ORDERS: dict[str, PeerMetricOrder] = {
    "per": PeerMetricOrder.ASCENDING,
    "pbr": PeerMetricOrder.ASCENDING,
    "roe": PeerMetricOrder.DESCENDING,
    "operating_margin": PeerMetricOrder.DESCENDING,
    "free_cash_flow_yield": PeerMetricOrder.DESCENDING,
    "revenue_yoy": PeerMetricOrder.DESCENDING,
}

PEER_PROFILE_METRICS: dict[PeerProfileAxis, tuple[str, ...]] = {
    PeerProfileAxis.PROFITABILITY: (
        "operating_margin",
        "roe",
    ),
    PeerProfileAxis.GROWTH: ("revenue_yoy",),
    PeerProfileAxis.VALUATION: (
        "per",
        "pbr",
    ),
    PeerProfileAxis.CASH_GENERATION: ("free_cash_flow_yield",),
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


class PeerProfileMetric(BaseModel):
    metric: str = Field(min_length=1)
    rank: int | None
    available_count: int = Field(ge=0)
    rank_fraction: float | None = Field(default=None, ge=0.0, le=1.0)
    band: PeerProfileBand


class PeerProfileAxisSummary(BaseModel):
    axis: PeerProfileAxis
    configured_metric_count: int = Field(ge=1)
    ranked_metric_count: int = Field(ge=0)
    first_third_count: int = Field(ge=0)
    middle_third_count: int = Field(ge=0)
    last_third_count: int = Field(ge=0)
    unranked_count: int = Field(ge=0)
    metrics: list[PeerProfileMetric]

    @model_validator(mode="after")
    def validate_counts(self) -> PeerProfileAxisSummary:
        if self.configured_metric_count != len(self.metrics):
            raise ValueError(
                "configured_metric_count must match profile metric count"
            )
        if self.ranked_metric_count + self.unranked_count != len(self.metrics):
            raise ValueError(
                "ranked_metric_count plus unranked_count must match metrics"
            )
        if (
            self.first_third_count
            + self.middle_third_count
            + self.last_third_count
            != self.ranked_metric_count
        ):
            raise ValueError(
                "profile band counts must match ranked_metric_count"
            )
        return self


class PeerProfileSet(BaseModel):
    subject_symbol: str = Field(min_length=1)
    axes: list[PeerProfileAxisSummary]

    def metric_values(self) -> dict[str, float | None]:
        result: dict[str, float | None] = {}
        for axis in self.axes:
            prefix = (
                f"peer:{self.subject_symbol}:profile:"
                f"{axis.axis.value}:"
            )
            result[f"{prefix}configured_metric_count"] = float(
                axis.configured_metric_count
            )
            result[f"{prefix}ranked_metric_count"] = float(
                axis.ranked_metric_count
            )
            result[f"{prefix}first_third_count"] = float(
                axis.first_third_count
            )
            result[f"{prefix}middle_third_count"] = float(
                axis.middle_third_count
            )
            result[f"{prefix}last_third_count"] = float(
                axis.last_third_count
            )
            result[f"{prefix}unranked_count"] = float(axis.unranked_count)
        return result

    def get(
        self,
        axis: PeerProfileAxis | str,
    ) -> PeerProfileAxisSummary | None:
        axis_value = PeerProfileAxis(axis)
        return next(
            (
                summary
                for summary in self.axes
                if summary.axis == axis_value
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


def build_peer_profile(
    positioning: PeerPositioningSet,
) -> PeerProfileSet:
    axes: list[PeerProfileAxisSummary] = []
    for axis, metrics in PEER_PROFILE_METRICS.items():
        profile_metrics = []
        for metric in metrics:
            position = positioning.get(metric)
            if position is None:
                raise PeerComparisonError(
                    f"peer positioning is missing configured metric: {metric}"
                )
            profile_metrics.append(_profile_metric(position))

        axes.append(
            _profile_axis_summary(
                axis,
                profile_metrics,
            )
        )

    return PeerProfileSet(
        subject_symbol=positioning.subject_symbol,
        axes=axes,
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


def _profile_metric(
    position: PeerMetricPosition,
) -> PeerProfileMetric:
    if position.rank is None or position.available_count < 2:
        return PeerProfileMetric(
            metric=position.metric,
            rank=position.rank,
            available_count=position.available_count,
            rank_fraction=None,
            band=PeerProfileBand.UNRANKED,
        )

    rank_fraction = (
        (position.rank - 1)
        / (position.available_count - 1)
    )
    if rank_fraction < (1 / 3):
        band = PeerProfileBand.FIRST_THIRD
    elif rank_fraction > (2 / 3):
        band = PeerProfileBand.LAST_THIRD
    else:
        band = PeerProfileBand.MIDDLE_THIRD

    return PeerProfileMetric(
        metric=position.metric,
        rank=position.rank,
        available_count=position.available_count,
        rank_fraction=rank_fraction,
        band=band,
    )


def _profile_axis_summary(
    axis: PeerProfileAxis,
    metrics: list[PeerProfileMetric],
) -> PeerProfileAxisSummary:
    ranked = [
        metric
        for metric in metrics
        if metric.band != PeerProfileBand.UNRANKED
    ]
    return PeerProfileAxisSummary(
        axis=axis,
        configured_metric_count=len(metrics),
        ranked_metric_count=len(ranked),
        first_third_count=sum(
            metric.band == PeerProfileBand.FIRST_THIRD
            for metric in metrics
        ),
        middle_third_count=sum(
            metric.band == PeerProfileBand.MIDDLE_THIRD
            for metric in metrics
        ),
        last_third_count=sum(
            metric.band == PeerProfileBand.LAST_THIRD
            for metric in metrics
        ),
        unranked_count=sum(
            metric.band == PeerProfileBand.UNRANKED
            for metric in metrics
        ),
        metrics=metrics,
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
