from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime

from universal_stock_skill.analysis import PeerAnalysisOrchestrator, StockAnalysisOrchestrator
from universal_stock_skill.data import (
    AnnualFilingDiscovery,
    EDINETCanonicalPipeline,
    EDINETClient,
    EDINETConfig,
    JQuantsConfig,
    JQuantsMarketDataSource,
)


async def run(symbol: str, peer_symbols: list[str], as_of: datetime, *, years: int) -> None:
    edinet_key = os.environ.get("EDINET_API_KEY")
    if not edinet_key:
        raise ValueError("EDINET_API_KEY is required")

    edinet = EDINETClient(EDINETConfig(api_key=edinet_key))
    market = JQuantsMarketDataSource(JQuantsConfig.from_env())

    try:
        stock = StockAnalysisOrchestrator(
            filing_discovery=AnnualFilingDiscovery(client=edinet),
            edinet_pipeline=EDINETCanonicalPipeline(client=edinet),
            market_source=market,
        )
        result = await PeerAnalysisOrchestrator(stock).analyze(
            symbol,
            peer_symbols=peer_symbols,
            as_of=as_of,
            years=years,
        )
    finally:
        await market.aclose()

    payload = {
        "subject": result.subject.model_dump(mode="json"),
        "peers": [peer.model_dump(mode="json") for peer in result.peers],
        "comparison": result.comparison.model_dump(mode="json"),
        "analysis_context": result.build_context().model_dump(mode="json"),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Analyze one subject and peer securities at the same point in time."
    )
    parser.add_argument("symbol")
    parser.add_argument("--peers", nargs="+", required=True)
    parser.add_argument("--as-of", required=True, help="Timezone-aware ISO 8601 timestamp.")
    parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args()

    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")
    if args.years < 1:
        parser.error("--years must be >= 1")

    asyncio.run(run(args.symbol, args.peers, as_of, years=args.years))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
