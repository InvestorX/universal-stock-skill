from __future__ import annotations

from universal_stock_skill.analysis.models import FinancialSnapshot, StockMetrics
from universal_stock_skill.finance import (
    free_cash_flow,
    free_cash_flow_yield,
    margin,
    pbr,
    per,
    roe,
    roic,
)


def calculate_stock_metrics(snapshot: FinancialSnapshot) -> StockMetrics:
    calculated_roic: float | None = None
    if snapshot.nopat is not None and snapshot.average_invested_capital is not None:
        calculated_roic = roic(snapshot.nopat, snapshot.average_invested_capital)

    return StockMetrics(
        operating_margin=margin(snapshot.operating_income, snapshot.revenue),
        per=per(snapshot.price, snapshot.eps),
        pbr=pbr(snapshot.price, snapshot.bps),
        roe=roe(snapshot.net_income, snapshot.average_equity),
        free_cash_flow=free_cash_flow(
            snapshot.operating_cash_flow,
            snapshot.capital_expenditure,
        ),
        free_cash_flow_yield=free_cash_flow_yield(
            snapshot.operating_cash_flow,
            snapshot.capital_expenditure,
            snapshot.market_cap,
        ),
        roic=calculated_roic,
    )
