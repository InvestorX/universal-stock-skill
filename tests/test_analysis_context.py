from datetime import UTC, datetime
from decimal import Decimal

import pytest

from universal_stock_skill.analysis.assembly import FinancialSnapshotAssemblyResult
from universal_stock_skill.analysis.bridge import SnapshotCanonicalReadiness
from universal_stock_skill.analysis.context import AnalysisContext, build_analysis_context
from universal_stock_skill.analysis.derivations import (
    DerivationMethod,
    DerivedFinancialInputs,
)
from universal_stock_skill.analysis.models import FinancialSnapshot, StockMetrics
from universal_stock_skill.analysis.orchestrator import (
    FilingSelectionSummary,
    StockAnalysisDataBundle,
)
from universal_stock_skill.analysis.report import EvidenceRef
from universal_stock_skill.analysis.trends import (
    CanonicalMetricTrend,
    CanonicalTrendSet,
)
from universal_stock_skill.data.canonical import CanonicalMetric
from universal_stock_skill.data.canonical_quality import CanonicalMappingQuality
from universal_stock_skill.data.market import MarketSnapshot
from universal_stock_skill.evidence.collection import EvidenceItem
from universal_stock_skill.evidence.models import SourceRecord


def bundle() -> StockAnalysisDataBundle:
    snapshot = FinancialSnapshot(
        symbol="7203",
        as_of=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
        price=3000,
        revenue=48_000,
        operating_income=6_000,
        net_income=5_000,
        eps=320,
        bps=2400,
        average_equity=30_000,
        operating_cash_flow=7_000,
        capital_expenditure=4_000,
        market_cap=40_000,
    )
    return StockAnalysisDataBundle(
        symbol="7203",
        requested_as_of=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
        filing=FilingSelectionSummary(
            original_doc_id="BASE",
            selected_doc_id="CORR",
            correction_doc_ids=["CORR"],
            is_corrected=True,
            filer_name="Demo Corp",
            period_start="2025-04-01",
            period_end="2026-03-31",
            published_at=datetime(2026, 7, 1, 1, 0, tzinfo=UTC),
        ),
        market=MarketSnapshot(
            symbol="7203",
            observed_at=datetime(2026, 9, 29, 6, 30, tzinfo=UTC),
            price=3000,
            currency="JPY",
            source="jquants:v2",
            market_cap=40_000,
        ),
        mapping_quality=CanonicalMappingQuality(
            requested_count=6,
            mapped_count=6,
            exact_count=6,
            fallback_count=0,
            missing_count=0,
            coverage_ratio=1.0,
            fallback_ratio=0.0,
            fallback_metrics=[],
            missing_metrics=[],
        ),
        snapshot_readiness=SnapshotCanonicalReadiness(
            ready=True,
            required_metrics=[
                CanonicalMetric.REVENUE,
                CanonicalMetric.OPERATING_INCOME,
                CanonicalMetric.NET_INCOME,
                CanonicalMetric.EPS,
                CanonicalMetric.BPS,
                CanonicalMetric.CF_OPERATING,
            ],
            missing_metrics=[],
            fallback_metrics=[],
        ),
        trends=CanonicalTrendSet(
            trends=[
                CanonicalMetricTrend(
                    metric=CanonicalMetric.REVENUE,
                    current_value=Decimal(48000),
                    prior_value=Decimal(44000),
                    year_over_year=0.0909,
                    cagr_value=0.07,
                    cagr_years=4,
                )
            ],
            missing=[],
        ),
        assembly=FinancialSnapshotAssemblyResult(
            snapshot=snapshot,
            derived=DerivedFinancialInputs(
                average_equity=Decimal(30000),
                average_equity_method=DerivationMethod.OFFICIAL_ROE_BACKSOLVE,
                capital_expenditure=Decimal(4000),
                capital_expenditure_method=DerivationMethod.CAPEX_COMPONENT_SUM,
            ),
        ),
        metrics=StockMetrics(
            operating_margin=0.125,
            per=9.375,
            pbr=1.25,
            roe=1 / 6,
            free_cash_flow=3_000,
            free_cash_flow_yield=0.075,
            roic=None,
        ),
    )


def test_context_builds_stable_evidence_and_metric_ids() -> None:
    context = build_analysis_context(bundle())

    assert context.symbol == "7203"
    assert context.evidence_ids == {
        "edinet:CORR",
        "market:jquants:v2:2026-09-29T06:30:00+00:00",
    }
    assert context.deterministic_metrics["metric:per"] == 9.375
    assert "trend:revenue" in context.trends
    assert any("ROIC is unavailable" in item for item in context.limitations)
    assert "Deterministic peer comparison data is unavailable." in context.limitations
    assert "News evidence is unavailable." in context.limitations


def test_context_rejects_future_evidence() -> None:
    with pytest.raises(ValueError, match="newer than requested_as_of"):
        AnalysisContext(
            symbol="7203",
            requested_as_of=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
            evidence=[
                EvidenceRef(
                    source_id="future:source",
                    title="Future source",
                    published_at=datetime(2026, 9, 30, 0, 0, tzinfo=UTC),
                )
            ],
            authoritative_facts={},
            deterministic_metrics={},
            trends={},
            derivations={},
            limitations=[],
        )


def test_context_can_include_qualitative_evidence_and_peer_metrics() -> None:
    subject = bundle()
    peer = bundle().model_copy(
        update={
            "symbol": "6758",
            "filing": bundle().filing.model_copy(
                update={
                    "original_doc_id": "PEER",
                    "selected_doc_id": "PEER",
                    "correction_doc_ids": [],
                    "is_corrected": False,
                    "filer_name": "Peer Corp",
                }
            ),
            "market": bundle().market.model_copy(
                update={
                    "symbol": "6758",
                    "price": 2500,
                    "market_cap": 50_000,
                }
            ),
            "assembly": bundle().assembly.model_copy(
                update={
                    "snapshot": bundle().assembly.snapshot.model_copy(
                        update={
                            "symbol": "6758",
                            "price": 2500,
                            "market_cap": 50_000,
                        }
                    )
                }
            ),
            "metrics": bundle().metrics.model_copy(
                update={
                    "per": 15.0,
                    "pbr": 1.5,
                }
            ),
        }
    )
    news = EvidenceItem(
        symbol="7203",
        excerpt="A point-in-time news excerpt.",
        tags=["earnings"],
        record=SourceRecord(
            source_id="news:demo",
            source_type="news",
            title="Demo news",
            published_at=datetime(2026, 9, 29, 10, 0, tzinfo=UTC),
            retrieved_at=datetime(2026, 9, 29, 11, 0, tzinfo=UTC),
            url="https://example.com/news/demo",
        ),
    )

    context = build_analysis_context(
        subject,
        evidence_items=[news],
        peer_bundles=[peer],
    )

    assert "news:demo" in context.evidence_ids
    assert "peer:6758:edinet:PEER" in context.evidence_ids
    assert context.peer_metrics["peer:6758:per"] == 15.0
    assert "peer_comparison" in context.authoritative_facts
    assert "qualitative_evidence" in context.authoritative_facts
    assert "Deterministic peer comparison data is unavailable." not in context.limitations
    assert "News evidence is unavailable." not in context.limitations
