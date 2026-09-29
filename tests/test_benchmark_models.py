from datetime import datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from universal_stock_skill.benchmark import BenchmarkCase


def test_point_in_time_blocks_future_publication() -> None:
    as_of = datetime(2026, 1, 10, 12, 0, tzinfo=timezone(timedelta(hours=9)))
    case = BenchmarkCase(
        case_id="case-001",
        symbol="7203",
        as_of=as_of,
        task="Analyze profitability.",
    )

    before = as_of - timedelta(minutes=1)
    after = as_of + timedelta(minutes=1)

    assert case.allows_publication(before)
    assert not case.allows_publication(after)


def test_as_of_requires_timezone() -> None:
    with pytest.raises(ValidationError):
        BenchmarkCase(
            case_id="case-001",
            symbol="7203",
            as_of="2026-01-10T12:00:00",
            task="Analyze profitability.",
        )
