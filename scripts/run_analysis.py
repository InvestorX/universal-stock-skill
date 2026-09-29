from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone

from universal_stock_skill.analysis import FinancialSnapshot, calculate_stock_metrics


def build_demo_snapshot(symbol: str) -> FinancialSnapshot:
    """Synthetic data only. Real market-data connectors are added in Phase 3."""
    return FinancialSnapshot(
        symbol=symbol,
        as_of=datetime(2026, 1, 1, tzinfo=timezone.utc),
        price=1000.0,
        revenue=10000.0,
        operating_income=1200.0,
        net_income=700.0,
        eps=100.0,
        bps=500.0,
        average_equity=5000.0,
        operating_cash_flow=1100.0,
        capital_expenditure=300.0,
        market_cap=10000.0,
        nopat=850.0,
        average_invested_capital=6000.0,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("symbol", nargs="?", default="DEMO")
    parser.add_argument(
        "--demo",
        action="store_true",
        help="Use synthetic financial data. No real market data is fetched.",
    )
    args = parser.parse_args()

    if not args.demo:
        parser.error("real market-data connectors are not implemented yet; use --demo")

    snapshot = build_demo_snapshot(args.symbol)
    metrics = calculate_stock_metrics(snapshot)

    print(
        json.dumps(
            {
                "warning": "synthetic demo data",
                "snapshot": snapshot.model_dump(mode="json"),
                "calculated_metrics": metrics.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
