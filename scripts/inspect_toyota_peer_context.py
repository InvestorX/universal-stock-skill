from __future__ import annotations

import argparse
import json
from datetime import datetime

from universal_stock_skill.benchmark import (
    toyota_automotive_peer_context,
    toyota_reference_market_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build Toyota 7203 AnalysisContext with Honda 7267 and Nissan "
            "7201 real-company peer reference rows."
        )
    )
    parser.add_argument("--toyota-price", type=float, required=True)
    parser.add_argument("--honda-price", type=float, required=True)
    parser.add_argument("--nissan-price", type=float, required=True)
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO 8601 market observation timestamp.",
    )
    args = parser.parse_args()

    observed_at = datetime.fromisoformat(args.as_of)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")

    context = toyota_automotive_peer_context(
        toyota_reference_market_snapshot(
            price=args.toyota_price,
            observed_at=observed_at,
        ),
        honda_price=args.honda_price,
        nissan_price=args.nissan_price,
    )

    print(
        json.dumps(
            context.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
