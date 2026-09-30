from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from universal_stock_skill.evidence.models import SourceRecord


class FutureInformationError(ValueError):
    pass


@dataclass(frozen=True)
class PointInTimeGuard:
    as_of: datetime

    def __post_init__(self) -> None:
        if self.as_of.tzinfo is None or self.as_of.utcoffset() is None:
            raise ValueError("as_of must be timezone-aware")

    def validate(self, record: SourceRecord) -> SourceRecord:
        if record.published_at > self.as_of:
            raise FutureInformationError(
                f"{record.source_id} was published at {record.published_at.isoformat()}, "
                f"after as_of={self.as_of.isoformat()}"
            )
        return record

    def validate_all(self, records: list[SourceRecord]) -> list[SourceRecord]:
        return [self.validate(record) for record in records]
