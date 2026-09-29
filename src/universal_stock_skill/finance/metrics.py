from __future__ import annotations


def _divide(numerator: float, denominator: float, *, name: str) -> float:
    if denominator == 0:
        raise ValueError(f"{name}: denominator must not be zero")
    return numerator / denominator


def margin(profit: float, revenue: float) -> float:
    """Return margin as a decimal ratio, e.g. 0.125 == 12.5%."""
    return _divide(profit, revenue, name="margin")


def cagr(begin_value: float, end_value: float, years: float) -> float:
    """Compound annual growth rate as a decimal ratio."""
    if begin_value <= 0 or end_value < 0:
        raise ValueError("cagr requires begin_value > 0 and end_value >= 0")
    if years <= 0:
        raise ValueError("cagr requires years > 0")
    return (end_value / begin_value) ** (1.0 / years) - 1.0


def per(price: float, eps: float) -> float:
    return _divide(price, eps, name="per")


def pbr(price: float, bps: float) -> float:
    return _divide(price, bps, name="pbr")


def roe(net_income: float, average_equity: float) -> float:
    return _divide(net_income, average_equity, name="roe")


def roic(nopat: float, average_invested_capital: float) -> float:
    return _divide(nopat, average_invested_capital, name="roic")


def free_cash_flow(operating_cash_flow: float, capital_expenditure: float) -> float:
    """FCF where capex is supplied as a positive cash outflow amount."""
    return operating_cash_flow - capital_expenditure


def free_cash_flow_yield(
    operating_cash_flow: float,
    capital_expenditure: float,
    market_cap: float,
) -> float:
    fcf = free_cash_flow(operating_cash_flow, capital_expenditure)
    return _divide(fcf, market_cap, name="free_cash_flow_yield")
