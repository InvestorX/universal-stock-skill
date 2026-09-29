from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from universal_stock_skill.analysis import calculate_canonical_trends
from universal_stock_skill.data import (
    DEFAULT_CANONICAL_MAPPER,
    CanonicalMetric,
    EDINETCsvArchive,
    evaluate_mapping_quality,
)

TREND_METRICS = [
    CanonicalMetric.REVENUE,
    CanonicalMetric.OPERATING_INCOME,
    CanonicalMetric.NET_INCOME,
    CanonicalMetric.EPS,
    CanonicalMetric.CF_OPERATING,
]


def build_inspection_payload(payload: bytes, *, years: int = 5) -> dict[str, Any]:
    facts = EDINETCsvArchive().parse(payload)
    canonical = DEFAULT_CANONICAL_MAPPER.resolve(facts)
    series = DEFAULT_CANONICAL_MAPPER.resolve_series(facts, years=years)
    trends = calculate_canonical_trends(series, TREND_METRICS)
    quality = evaluate_mapping_quality(canonical)

    return {
        "fact_count": len(facts),
        "current": canonical.model_dump(mode="json"),
        "mapping_quality": quality.model_dump(mode="json"),
        "series": series.model_dump(mode="json"),
        "trends": trends.model_dump(mode="json"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Inspect canonical mappings, historical series, and trends "
            "from an EDINET type=5 ZIP file."
        )
    )
    parser.add_argument("zip_path", type=Path)
    parser.add_argument("--years", type=int, default=5)
    args = parser.parse_args()

    result = build_inspection_payload(
        args.zip_path.read_bytes(),
        years=args.years,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
