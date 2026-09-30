from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime

from universal_stock_skill.analysis import StockAnalysisOrchestrator
from universal_stock_skill.data import (
    AnnualFilingDiscovery,
    EDINETCanonicalPipeline,
    EDINETClient,
    EDINETConfig,
    JQuantsConfig,
    JQuantsMarketDataSource,
)


async def run(symbol: str, as_of: datetime, *, years: int) -> None:
    edinet_key = os.environ.get("EDINET_API_KEY")
    if not edinet_key:
        raise ValueError("EDINET_API_KEY is required")

    edinet = EDINETClient(EDINETConfig(api_key=edinet_key))
    market = JQuantsMarketDataSource(JQuantsConfig.from_env())

    try:
        orchestrator = StockAnalysisOrchestrator(
            filing_discovery=AnnualFilingDiscovery(client=edinet),
            edinet_pipeline=EDINETCanonicalPipeline(client=edinet),
            market_source=market,
        )
        result = await orchestrator.analyze(
            symbol,
            as_of=as_of,
            years=years,
        )
    finally:
        await market.aclose()

    print(
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build a deterministic stock-analysis data bundle from "
            "EDINET and J-Quants."
        )
    )
    parser.add_argument("symbol")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO 8601 timestamp.",
    )
    parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args()

    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")
    if args.years < 1:
        parser.error("--years must be >= 1")

    asyncio.run(run(args.symbol, as_of, years=args.years))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
