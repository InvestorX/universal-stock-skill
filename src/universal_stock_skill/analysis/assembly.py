from __future__ import annotations

from pydantic import BaseModel

from universal_stock_skill.analysis.bridge import (
    build_financial_snapshot,
    evaluate_snapshot_readiness,
)
from universal_stock_skill.analysis.derivations import (
    DerivedFinancialInputs,
    derive_financial_inputs,
)
from universal_stock_skill.analysis.market_bridge import (
    SnapshotDerivedInputs,
    build_snapshot_bridge_inputs,
)
from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.data.canonical import (
    CanonicalFinancialSeries,
    CanonicalFinancialSet,
)
from universal_stock_skill.data.market import MarketSnapshot


class FinancialSnapshotAssemblyError(ValueError):
    pass


class FinancialSnapshotAssemblyResult(BaseModel):
    snapshot: FinancialSnapshot
    derived: DerivedFinancialInputs


def assemble_financial_snapshot(
    current: CanonicalFinancialSet,
    series: CanonicalFinancialSeries,
    market: MarketSnapshot,
) -> FinancialSnapshotAssemblyResult:
    readiness = evaluate_snapshot_readiness(current)
    if not readiness.ready:
        missing = ", ".join(metric.value for metric in readiness.missing_metrics)
        raise FinancialSnapshotAssemblyError(
            f"filing-side canonical metrics are missing: {missing}"
        )

    derived = derive_financial_inputs(current, series)
    if derived.average_equity is None:
        raise FinancialSnapshotAssemblyError(
            "average_equity could not be derived safely"
        )
    if derived.capital_expenditure is None:
        raise FinancialSnapshotAssemblyError(
            "capital_expenditure could not be derived safely"
        )

    bridge_inputs = build_snapshot_bridge_inputs(
        market,
        SnapshotDerivedInputs(
            average_equity=float(derived.average_equity),
            capital_expenditure=float(derived.capital_expenditure),
            nopat=(
                float(derived.nopat)
                if derived.nopat is not None
                else None
            ),
            average_invested_capital=(
                float(derived.average_invested_capital)
                if derived.average_invested_capital is not None
                else None
            ),
        ),
    )

    snapshot = build_financial_snapshot(current, bridge_inputs)
    return FinancialSnapshotAssemblyResult(
        snapshot=snapshot,
        derived=derived,
    )
