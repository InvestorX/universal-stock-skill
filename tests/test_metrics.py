import pytest

from universal_stock_skill.finance import cagr, free_cash_flow, margin, pbr, per


def test_common_financial_metrics() -> None:
    assert margin(20.0, 100.0) == pytest.approx(0.20)
    assert per(3000.0, 300.0) == pytest.approx(10.0)
    assert pbr(3000.0, 1500.0) == pytest.approx(2.0)
    assert free_cash_flow(500.0, 120.0) == pytest.approx(380.0)


def test_cagr() -> None:
    assert cagr(100.0, 121.0, 2.0) == pytest.approx(0.10)


def test_zero_denominator_is_rejected() -> None:
    with pytest.raises(ValueError):
        per(1000.0, 0.0)
