from decimal import Decimal

import pytest

from universal_stock_skill.benchmark.reference import pct_change, ratio
from universal_stock_skill.benchmark.toyota import toyota_7203_reference_case
from universal_stock_skill.evidence.collection import EvidenceCollector


class FixtureEvidenceSource:
    async def search(
        self,
        symbol: str,
        *,
        as_of,
        limit: int = 20,
    ):
        case = toyota_7203_reference_case()
        return case.qualitative_evidence[:limit]


def test_toyota_fy2026_official_financial_values_are_frozen() -> None:
    case = toyota_7203_reference_case()
    current = case.period("FY2026")
    prior = case.period("FY2025")

    assert case.symbol == "7203"
    assert case.company_name == "Toyota Motor Corporation"
    assert case.accounting_standard == "IFRS"

    assert current.values_million_yen["revenue"] == Decimal(50_684_952)
    assert current.values_million_yen["operating_income"] == Decimal(3_766_216)
    assert (
        current.values_million_yen["net_income_attributable_to_parent"]
        == Decimal(3_848_098)
    )
    assert current.per_share_yen["eps_basic"] == Decimal("295.25")
    assert current.per_share_yen["bps"] == Decimal("3062.82")
    assert current.ratios["roe"] == Decimal("0.101")

    assert prior.values_million_yen["revenue"] == Decimal(48_036_704)
    assert prior.ratios["roe"] == Decimal("0.136")


def test_toyota_reference_recalculations_match_official_rounded_ratios() -> None:
    case = toyota_7203_reference_case()
    current = case.period("FY2026")
    prior = case.period("FY2025")

    operating_margin = ratio(
        current.values_million_yen["operating_income"],
        current.values_million_yen["revenue"],
    )
    revenue_yoy = pct_change(
        current.values_million_yen["revenue"],
        prior.values_million_yen["revenue"],
    )
    operating_income_yoy = pct_change(
        current.values_million_yen["operating_income"],
        prior.values_million_yen["operating_income"],
    )
    parent_income_yoy = pct_change(
        current.values_million_yen["net_income_attributable_to_parent"],
        prior.values_million_yen["net_income_attributable_to_parent"],
    )

    assert float(operating_margin) == pytest.approx(0.0743063937)
    assert round(float(operating_margin) * 100, 1) == 7.4
    assert round(float(revenue_yoy) * 100, 1) == 5.5
    assert round(float(operating_income_yoy) * 100, 1) == -21.5
    assert round(float(parent_income_yoy) * 100, 1) == -19.2


def test_toyota_two_period_equity_reproduces_official_roe_with_rounding() -> None:
    case = toyota_7203_reference_case()
    current = case.period("FY2026")
    prior = case.period("FY2025")

    average_equity = (
        current.values_million_yen["owners_equity"]
        + prior.values_million_yen["owners_equity"]
    ) / Decimal(2)
    calculated_roe = ratio(
        current.values_million_yen["net_income_attributable_to_parent"],
        average_equity,
    )

    assert average_equity == Decimal(37_921_840)
    assert round(float(calculated_roe) * 100, 1) == 10.1


def test_toyota_effective_tax_rate_and_nopat_are_deterministic() -> None:
    case = toyota_7203_reference_case()
    current = case.period("FY2026")

    tax_rate = ratio(
        current.values_million_yen["income_tax_expense"],
        current.values_million_yen["profit_before_tax"],
    )
    nopat = current.values_million_yen["operating_income"] * (
        Decimal(1) - tax_rate
    )

    assert float(tax_rate) == pytest.approx(0.2265136612)
    assert float(nopat) == pytest.approx(2_913_167.206, rel=1e-6)


@pytest.mark.asyncio
async def test_toyota_official_ir_evidence_passes_point_in_time_collection() -> None:
    case = toyota_7203_reference_case()
    collector = EvidenceCollector(sources=[FixtureEvidenceSource()])

    result = await collector.collect(
        case.symbol,
        as_of=case.as_of,
    )

    assert [item.record.source_id for item in result] == [
        "toyota:ir:2026-buyback",
        "toyota:ir:fy2027-q1-results",
        "toyota:ir:fy2026-results",
    ]
    assert result[0].record.metadata["maximum_repurchase_price_jpy"] == (
        1_000_000_000_000
    )
