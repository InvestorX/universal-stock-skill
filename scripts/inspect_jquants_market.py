from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime

from universal_stock_skill.data import (
    JQuantsConfig,
    JQuantsMarketDataSource,
)


async def run(symbol: str, as_of: datetime) -> None:
    source = JQuantsMarketDataSource(JQuantsConfig.from_env())
    try:
        snapshot = await source.get_market_snapshot(symbol, as_of)
    finally:
        await source.aclose()

    print(
        json.dumps(
            snapshot.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect a point-in-time J-Quants MarketSnapshot."
    )
    parser.add_argument("symbol")
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO 8601 timestamp, e.g. 2026-09-29T16:00:00+09:00",
    )
    args = parser.parse_args()

    as_of = datetime.fromisoformat(args.as_of)
    if as_of.tzinfo is None or as_of.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")

    asyncio.run(run(args.symbol, as_of))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
