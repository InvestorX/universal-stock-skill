from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from universal_stock_skill.benchmark.automotive_peers import (
    honda_7267_reference,
    nissan_7201_reference,
    toyota_automotive_peer_context,
    toyota_honda_nissan_peer_comparison,
)
from universal_stock_skill.benchmark.toyota_analysis import (
    analyze_toyota_reference,
    toyota_reference_market_snapshot,
)

JST = ZoneInfo("Asia/Tokyo")


def toyota_analysis():
    return analyze_toyota_reference(
        toyota_reference_market_snapshot(
            price=3000,
            observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        )
    )


def test_real_peer_reference_periods_align_by_period_end_not_label() -> None:
    honda = honda_7267_reference()
    nissan = nissan_7201_reference()

    assert honda.period_end == nissan.period_end
    assert honda.period_end.isoformat() == "2026-03-31"
    assert honda.issuer_fiscal_label == "FYE March 31, 2026"
    assert nissan.issuer_fiscal_label == "FY2025"


def test_honda_reference_metrics_match_official_results() -> None:
    honda = honda_7267_reference()
    row = honda.row(
        price=1500,
        market_observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        requested_as_of=datetime(2026, 9, 29, 23, 59, tzinfo=JST),
    )

    assert row.revenue_yoy == pytest.approx(0.0049722974)
    assert row.operating_margin == pytest.approx(-0.019)
    assert row.roe == pytest.approx(-0.035)
    assert row.per is None
    assert row.pbr == pytest.approx(0.49408579)
    assert row.market_cap == pytest.approx(5_838_870_661_500)
    assert row.free_cash_flow_yield == pytest.approx(0.0407126675)


def test_nissan_reference_metrics_keep_noncomparable_fcf_unavailable() -> None:
    nissan = nissan_7201_reference()
    row = nissan.row(
        price=350,
        market_observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        requested_as_of=datetime(2026, 9, 29, 23, 59, tzinfo=JST),
    )

    assert row.revenue_yoy == pytest.approx(-0.0494985678)
    assert row.operating_margin == pytest.approx(0.005)
    assert row.roe == pytest.approx(-0.109)
    assert row.per is None
    assert row.pbr == pytest.approx(0.25499796)
    assert row.market_cap == pytest.approx(1_223_733_882_000)
    assert row.free_cash_flow_yield is None


def test_toyota_honda_nissan_comparison_exposes_grounding_ids() -> None:
    comparison, evidence = toyota_honda_nissan_peer_comparison(
        toyota_analysis(),
        honda_price=1500,
        nissan_price=350,
    )

    values = comparison.metric_values()

    assert [row.symbol for row in comparison.rows] == [
        "7203",
        "7267",
        "7201",
    ]
    assert values["peer:7203:operating_margin"] == pytest.approx(0.0743063937)
    assert values["peer:7267:operating_margin"] == pytest.approx(-0.019)
    assert values["peer:7201:operating_margin"] == pytest.approx(0.005)
    assert values["peer:7267:roe"] == pytest.approx(-0.035)
    assert values["peer:7201:roe"] == pytest.approx(-0.109)
    assert values["peer:7201:free_cash_flow_yield"] is None

    assert {item.record.source_id for item in evidence} == {
        "peer:7267:ir:fy2026-results",
        "peer:7267:ir:fy2026-cashflow-reference",
        "peer:7201:ir:fy2025-results",
    }


def test_toyota_peer_context_removes_missing_peer_limitation() -> None:
    context = toyota_automotive_peer_context(
        toyota_reference_market_snapshot(
            price=3000,
            observed_at=datetime(2026, 9, 29, 15, 30, tzinfo=JST),
        ),
        honda_price=1500,
        nissan_price=350,
    )

    assert "peer:7267:operating_margin" in context.metric_ids
    assert "peer:7201:revenue_yoy" in context.metric_ids
    assert "peer:7267:ir:fy2026-results" in context.evidence_ids
    assert "peer:7201:ir:fy2025-results" in context.evidence_ids
    assert (
        "Deterministic peer comparison data is unavailable."
        not in context.limitations
    )
    assert any(
        "PER is therefore unavailable" in item
        for item in context.limitations
    )
