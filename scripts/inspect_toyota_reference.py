from __future__ import annotations

import json

from universal_stock_skill.benchmark import toyota_7203_reference_case


def main() -> int:
    case = toyota_7203_reference_case()
    print(
        json.dumps(
            case.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
