import pytest

from universal_stock_skill.analysis.peers import (
    PeerComparisonError,
    PeerMetricOrder,
    PeerMetricPosition,
    PeerPositioningSet,
    PeerProfileAxis,
    PeerProfileBand,
    build_peer_profile,
)


def position(
    metric: str,
    *,
    rank: int | None,
    available_count: int,
) -> PeerMetricPosition:
    return PeerMetricPosition(
        metric=metric,
        order=(
            PeerMetricOrder.ASCENDING
            if metric in {"per", "pbr"}
            else PeerMetricOrder.DESCENDING
        ),
        subject_value=1.0 if rank is not None else None,
        rank=rank,
        available_count=available_count,
        peer_available_count=max(available_count - 1, 0),
        comparison_median=1.0,
        delta_to_median=0.0 if rank is not None else None,
        peer_mean=1.0 if available_count > 1 else None,
        delta_to_peer_mean=0.0 if rank is not None else None,
    )


def positioning() -> PeerPositioningSet:
    return PeerPositioningSet(
        subject_symbol="AAA",
        positions=[
            position("per", rank=None, available_count=1),
            position("pbr", rank=2, available_count=4),
            position("roe", rank=3, available_count=5),
            position("operating_margin", rank=1, available_count=5),
            position("free_cash_flow_yield", rank=2, available_count=2),
            position("revenue_yoy", rank=5, available_count=5),
        ],
    )


def test_peer_profile_groups_metrics_into_four_axes() -> None:
    profile = build_peer_profile(positioning())

    assert profile.subject_symbol == "AAA"
    assert [axis.axis for axis in profile.axes] == [
        PeerProfileAxis.PROFITABILITY,
        PeerProfileAxis.GROWTH,
        PeerProfileAxis.VALUATION,
        PeerProfileAxis.CASH_GENERATION,
    ]

    profitability = profile.get(PeerProfileAxis.PROFITABILITY)
    assert profitability is not None
    assert profitability.configured_metric_count == 2
    assert profitability.ranked_metric_count == 2
    assert profitability.first_third_count == 1
    assert profitability.middle_third_count == 1
    assert profitability.last_third_count == 0
    assert profitability.unranked_count == 0

    growth = profile.get("growth")
    assert growth is not None
    assert growth.configured_metric_count == 1
    assert growth.ranked_metric_count == 1
    assert growth.last_third_count == 1

    valuation = profile.get("valuation")
    assert valuation is not None
    assert valuation.configured_metric_count == 2
    assert valuation.ranked_metric_count == 1
    assert valuation.middle_third_count == 1
    assert valuation.unranked_count == 1

    cash = profile.get("cash_generation")
    assert cash is not None
    assert cash.configured_metric_count == 1
    assert cash.ranked_metric_count == 1
    assert cash.last_third_count == 1


def test_peer_profile_uses_normalized_rank_thirds() -> None:
    profile = build_peer_profile(positioning())

    profitability = profile.get("profitability")
    assert profitability is not None
    margin = next(
        metric
        for metric in profitability.metrics
        if metric.metric == "operating_margin"
    )
    roe = next(
        metric
        for metric in profitability.metrics
        if metric.metric == "roe"
    )

    assert margin.rank_fraction == pytest.approx(0.0)
    assert margin.band == PeerProfileBand.FIRST_THIRD
    assert roe.rank_fraction == pytest.approx(0.5)
    assert roe.band == PeerProfileBand.MIDDLE_THIRD

    valuation = profile.get("valuation")
    assert valuation is not None
    per = next(metric for metric in valuation.metrics if metric.metric == "per")
    pbr = next(metric for metric in valuation.metrics if metric.metric == "pbr")

    assert per.rank_fraction is None
    assert per.band == PeerProfileBand.UNRANKED
    assert pbr.rank_fraction == pytest.approx(1 / 3)
    assert pbr.band == PeerProfileBand.MIDDLE_THIRD


def test_peer_profile_exposes_axis_count_metric_ids_without_overall_score() -> None:
    profile = build_peer_profile(positioning())

    values = profile.metric_values()

    assert values[
        "peer:AAA:profile:profitability:configured_metric_count"
    ] == 2.0
    assert values[
        "peer:AAA:profile:profitability:first_third_count"
    ] == 1.0
    assert values[
        "peer:AAA:profile:valuation:ranked_metric_count"
    ] == 1.0
    assert values[
        "peer:AAA:profile:valuation:unranked_count"
    ] == 1.0
    assert not any("score" in metric_id for metric_id in values)
    assert not any("overall" in metric_id for metric_id in values)


def test_peer_profile_rejects_missing_configured_position() -> None:
    incomplete = positioning().model_copy(
        update={
            "positions": [
                item
                for item in positioning().positions
                if item.metric != "roe"
            ]
        }
    )

    with pytest.raises(PeerComparisonError, match="missing configured metric"):
        build_peer_profile(incomplete)
