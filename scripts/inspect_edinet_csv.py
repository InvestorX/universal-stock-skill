from __future__ import annotations

import argparse
import json
from pathlib import Path

from universal_stock_skill.data import DEFAULT_CANONICAL_MAPPER, EDINETCsvArchive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect canonical financial mappings from an EDINET type=5 ZIP file."
    )
    parser.add_argument("zip_path", type=Path)
    args = parser.parse_args()

    payload = args.zip_path.read_bytes()
    facts = EDINETCsvArchive().parse(payload)
    canonical = DEFAULT_CANONICAL_MAPPER.resolve(facts)

    print(
        json.dumps(
            canonical.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
