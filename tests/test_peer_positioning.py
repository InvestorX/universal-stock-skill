from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis.peers import (
    PeerComparisonError,
    PeerComparisonSet,
    PeerMetricOrder,
    PeerMetricRow,
    build_peer_positioning,
)

AS_OF = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


def row(
    symbol: str,
    *,
    per: float | None,
    pbr: float | None = 1.0,
    roe: float | None = 0.1,
    operating_margin: float | None = 0.1,
    free_cash_flow_yield: float | None = 0.04,
    revenue_yoy: float | None = 0.08,
) -> PeerMetricRow:
    return PeerMetricRow(
        symbol=symbol,
        requested_as_of=AS_OF,
        market_observed_at=AS_OF,
        market_cap=1000,
        price=100,
        per=per,
        pbr=pbr,
        roe=roe,
        operating_margin=operating_margin,
        free_cash_flow_yield=free_cash_flow_yield,
        revenue_yoy=revenue_yoy,
    )


def comparison(*rows: PeerMetricRow) -> PeerComparisonSet:
    return PeerComparisonSet(
        subject_symbol="AAA",
        requested_as_of=AS_OF,
        rows=list(rows),
    )


def test_peer_positioning_calculates_rank_median_and_peer_mean() -> None:
    result = build_peer_positioning(
        comparison(
            row(
                "AAA",
                per=12,
                pbr=1.4,
                roe=0.12,
                operating_margin=0.10,
                free_cash_flow_yield=0.04,
                revenue_yoy=0.08,
            ),
            row(
                "BBB",
                per=10,
                pbr=1.8,
                roe=0.08,
                operating_margin=0.06,
                free_cash_flow_yield=0.05,
                revenue_yoy=0.08,
            ),
            row(
                "CCC",
                per=14,
                pbr=1.2,
                roe=0.15,
                operating_margin=0.04,
                free_cash_flow_yield=None,
                revenue_yoy=-0.02,
            ),
        )
    )

    per = result.get("per")
    assert per is not None
    assert per.order == PeerMetricOrder.ASCENDING
    assert per.rank == 2
    assert per.available_count == 3
    assert per.peer_available_count == 2
    assert per.comparison_median == pytest.approx(12)
    assert per.delta_to_median == pytest.approx(0)
    assert per.peer_mean == pytest.approx(12)
    assert per.delta_to_peer_mean == pytest.approx(0)

    margin = result.get("operating_margin")
    assert margin is not None
    assert margin.order == PeerMetricOrder.DESCENDING
    assert margin.rank == 1
    assert margin.comparison_median == pytest.approx(0.06)
    assert margin.delta_to_median == pytest.approx(0.04)
    assert margin.peer_mean == pytest.approx(0.05)
    assert margin.delta_to_peer_mean == pytest.approx(0.05)

    revenue = result.get("revenue_yoy")
    assert revenue is not None
    assert revenue.rank == 1


def test_peer_positioning_handles_missing_subject_metric() -> None:
    result = build_peer_positioning(
        comparison(
            row("AAA", per=None),
            row("BBB", per=10),
            row("CCC", per=14),
        )
    )

    per = result.get("per")
    assert per is not None
    assert per.rank is None
    assert per.available_count == 2
    assert per.peer_available_count == 2
    assert per.comparison_median == pytest.approx(12)
    assert per.peer_mean == pytest.approx(12)
    assert per.delta_to_median is None
    assert per.delta_to_peer_mean is None


def test_peer_positioning_suppresses_rank_with_only_one_available_value() -> None:
    result = build_peer_positioning(
        comparison(
            row("AAA", per=12),
            row("BBB", per=None),
            row("CCC", per=None),
        )
    )

    per = result.get("per")
    assert per is not None
    assert per.rank is None
    assert per.available_count == 1
    assert per.peer_available_count == 0


def test_peer_positioning_exposes_groundable_metric_ids() -> None:
    result = build_peer_positioning(
        comparison(
            row("AAA", per=12, operating_margin=0.10),
            row("BBB", per=15, operating_margin=0.05),
        )
    )

    values = result.metric_values()

    assert values["peer:AAA:position:per:rank"] == 1.0
    assert values["peer:AAA:position:per:available_count"] == 2.0
    assert values["peer:AAA:position:operating_margin:rank"] == 1.0
    assert values[
        "peer:AAA:position:operating_margin:delta_to_peer_mean"
    ] == pytest.approx(0.05)


def test_peer_positioning_requires_exactly_one_subject_row() -> None:
    with pytest.raises(PeerComparisonError, match="exactly one subject"):
        build_peer_positioning(
            PeerComparisonSet(
                subject_symbol="AAA",
                requested_as_of=AS_OF,
                rows=[row("BBB", per=10), row("CCC", per=14)],
            )
        )


def test_peer_positioning_rejects_duplicate_row_symbols() -> None:
    with pytest.raises(PeerComparisonError, match="row symbols must be unique"):
        build_peer_positioning(
            comparison(
                row("AAA", per=12),
                row("BBB", per=10),
                row("BBB", per=14),
            )
        )
