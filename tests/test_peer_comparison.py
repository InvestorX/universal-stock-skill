from datetime import UTC, datetime
from decimal import Decimal

import pytest

from universal_stock_skill.analysis.assembly import FinancialSnapshotAssemblyResult
from universal_stock_skill.analysis.bridge import SnapshotCanonicalReadiness
from universal_stock_skill.analysis.derivations import DerivedFinancialInputs
from universal_stock_skill.analysis.models import FinancialSnapshot, StockMetrics
from universal_stock_skill.analysis.orchestrator import (
    FilingSelectionSummary,
    StockAnalysisDataBundle,
)
from universal_stock_skill.analysis.peers import (
    PeerComparisonError,
    build_peer_comparison,
)
from universal_stock_skill.analysis.trends import (
    CanonicalMetricTrend,
    CanonicalTrendSet,
)
from universal_stock_skill.data.canonical import CanonicalMetric
from universal_stock_skill.data.canonical_quality import CanonicalMappingQuality
from universal_stock_skill.data.market import MarketSnapshot


def bundle(
    symbol: str,
    *,
    as_of: datetime,
    per: float,
    revenue_yoy: float,
) -> StockAnalysisDataBundle:
    snapshot = FinancialSnapshot(
        symbol=symbol,
        as_of=as_of,
        price=100,
        revenue=1000,
        operating_income=100,
        net_income=50,
        eps=10,
        bps=50,
        average_equity=500,
        operating_cash_flow=80,
        capital_expenditure=20,
        market_cap=10000,
    )
    return StockAnalysisDataBundle(
        symbol=symbol,
        requested_as_of=as_of,
        filing=FilingSelectionSummary(
            original_doc_id=f"{symbol}-BASE",
            selected_doc_id=f"{symbol}-BASE",
            correction_doc_ids=[],
            is_corrected=False,
            filer_name=f"Company {symbol}",
            period_start="2025-04-01",
            period_end="2026-03-31",
            published_at=as_of,
        ),
        market=MarketSnapshot(
            symbol=symbol,
            observed_at=as_of,
            price=100,
            currency="JPY",
            source="fixture",
            market_cap=10000,
        ),
        mapping_quality=CanonicalMappingQuality(
            requested_count=6,
            mapped_count=6,
            exact_count=6,
            fallback_count=0,
            missing_count=0,
            coverage_ratio=1,
            fallback_ratio=0,
            fallback_metrics=[],
            missing_metrics=[],
        ),
        snapshot_readiness=SnapshotCanonicalReadiness(
            ready=True,
            required_metrics=[],
            missing_metrics=[],
            fallback_metrics=[],
        ),
        trends=CanonicalTrendSet(
            trends=[
                CanonicalMetricTrend(
                    metric=CanonicalMetric.REVENUE,
                    current_value=Decimal(1000),
                    prior_value=Decimal(900),
                    year_over_year=revenue_yoy,
                )
            ],
            missing=[],
        ),
        assembly=FinancialSnapshotAssemblyResult(
            snapshot=snapshot,
            derived=DerivedFinancialInputs(),
        ),
        metrics=StockMetrics(
            operating_margin=0.1,
            per=per,
            pbr=2,
            roe=0.1,
            free_cash_flow=60,
            free_cash_flow_yield=0.006,
            roic=None,
        ),
    )


def test_peer_comparison_exposes_deterministic_metric_ids() -> None:
    as_of = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    result = build_peer_comparison(
        bundle("7203", as_of=as_of, per=12, revenue_yoy=0.10),
        [bundle("6758", as_of=as_of, per=15, revenue_yoy=0.05)],
    )

    values = result.metric_values()

    assert result.subject_symbol == "7203"
    assert [row.symbol for row in result.rows] == ["7203", "6758"]
    assert values["peer:7203:per"] == 12
    assert values["peer:6758:per"] == 15
    assert values["peer:6758:revenue_yoy"] == 0.05


def test_peer_comparison_requires_same_as_of() -> None:
    first = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)
    second = datetime(2026, 9, 29, 13, 0, tzinfo=UTC)

    with pytest.raises(PeerComparisonError, match="same requested_as_of"):
        build_peer_comparison(
            bundle("7203", as_of=first, per=12, revenue_yoy=0.10),
            [bundle("6758", as_of=second, per=15, revenue_yoy=0.05)],
        )


def test_peer_comparison_rejects_duplicate_symbol() -> None:
    as_of = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)

    with pytest.raises(PeerComparisonError, match="unique"):
        build_peer_comparison(
            bundle("7203", as_of=as_of, per=12, revenue_yoy=0.10),
            [bundle("7203", as_of=as_of, per=15, revenue_yoy=0.05)],
        )
