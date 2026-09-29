from __future__ import annotations

import argparse
import json
from datetime import datetime

from universal_stock_skill.benchmark import (
    analyze_toyota_reference,
    toyota_reference_market_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the Toyota 7203 frozen financial reference case through the "
            "existing deterministic analysis pipeline."
        )
    )
    parser.add_argument(
        "--price",
        type=float,
        required=True,
        help="Reference market price in JPY/share.",
    )
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO 8601 timestamp for the reference market snapshot.",
    )
    args = parser.parse_args()

    observed_at = datetime.fromisoformat(args.as_of)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")

    market = toyota_reference_market_snapshot(
        price=args.price,
        observed_at=observed_at,
    )
    result = analyze_toyota_reference(market)

    print(
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
