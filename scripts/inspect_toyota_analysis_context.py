from __future__ import annotations

import argparse
import json
from datetime import datetime

from universal_stock_skill.benchmark import (
    toyota_reference_analysis_context,
    toyota_reference_market_snapshot,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Build the Toyota 7203 grounded AnalysisContext from the frozen "
            "reference case and an explicitly supplied market input."
        )
    )
    parser.add_argument("--price", type=float, required=True)
    parser.add_argument(
        "--as-of",
        required=True,
        help="Timezone-aware ISO 8601 market observation timestamp.",
    )
    args = parser.parse_args()

    observed_at = datetime.fromisoformat(args.as_of)
    if observed_at.tzinfo is None or observed_at.utcoffset() is None:
        parser.error("--as-of must include a timezone offset")

    context = toyota_reference_analysis_context(
        toyota_reference_market_snapshot(
            price=args.price,
            observed_at=observed_at,
        )
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
