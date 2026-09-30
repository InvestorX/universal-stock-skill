from datetime import UTC, datetime, timedelta

import pytest

from universal_stock_skill.evidence import (
    FutureInformationError,
    PointInTimeGuard,
    SourceRecord,
)


def source(published_at: datetime) -> SourceRecord:
    return SourceRecord(
        source_id="example",
        source_type="filing",
        title="Example filing",
        published_at=published_at,
        retrieved_at=datetime.now(UTC),
    )


def test_guard_accepts_information_available_at_as_of() -> None:
    as_of = datetime(2026, 1, 10, tzinfo=UTC)
    record = source(as_of - timedelta(seconds=1))
    assert PointInTimeGuard(as_of).validate(record) == record


def test_guard_rejects_future_information() -> None:
    as_of = datetime(2026, 1, 10, tzinfo=UTC)
    record = source(as_of + timedelta(seconds=1))

    with pytest.raises(FutureInformationError):
        PointInTimeGuard(as_of).validate(record)
