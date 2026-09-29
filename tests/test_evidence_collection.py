from datetime import UTC, datetime

import pytest

from universal_stock_skill.evidence.collection import (
    EvidenceCollectionError,
    EvidenceCollector,
    EvidenceItem,
)
from universal_stock_skill.evidence.guard import FutureInformationError
from universal_stock_skill.evidence.models import SourceRecord


def item(
    source_id: str,
    *,
    published_at: datetime,
    symbol: str = "7203",
    content_hash: str | None = None,
) -> EvidenceItem:
    return EvidenceItem(
        symbol=symbol,
        excerpt=f"excerpt:{source_id}",
        tags=["earnings"],
        record=SourceRecord(
            source_id=source_id,
            source_type="news",
            title=source_id,
            published_at=published_at,
            retrieved_at=datetime(2026, 9, 29, 12, 0, tzinfo=UTC),
            content_hash=content_hash,
        ),
    )


class FakeSource:
    def __init__(self, items: list[EvidenceItem]) -> None:
        self.items = items

    async def search(
        self,
        symbol: str,
        *,
        as_of: datetime,
        limit: int = 20,
    ) -> list[EvidenceItem]:
        return self.items[:limit]


@pytest.mark.asyncio
async def test_collector_deduplicates_by_content_hash_and_sorts_latest_first() -> None:
    collector = EvidenceCollector(
        sources=[
            FakeSource(
                [
                    item(
                        "news:older",
                        published_at=datetime(2026, 9, 28, 1, 0, tzinfo=UTC),
                        content_hash="same",
                    ),
                    item(
                        "news:newer",
                        published_at=datetime(2026, 9, 29, 1, 0, tzinfo=UTC),
                        content_hash="same",
                    ),
                    item(
                        "news:other",
                        published_at=datetime(2026, 9, 29, 2, 0, tzinfo=UTC),
                        content_hash="other",
                    ),
                ]
            )
        ]
    )

    result = await collector.collect(
        "7203",
        as_of=datetime(2026, 9, 29, 3, 0, tzinfo=UTC),
    )

    assert [value.record.source_id for value in result] == [
        "news:other",
        "news:newer",
    ]


@pytest.mark.asyncio
async def test_collector_rejects_future_evidence() -> None:
    collector = EvidenceCollector(
        sources=[
            FakeSource(
                [
                    item(
                        "news:future",
                        published_at=datetime(2026, 9, 30, 0, 0, tzinfo=UTC),
                    )
                ]
            )
        ]
    )

    with pytest.raises(FutureInformationError):
        await collector.collect(
            "7203",
            as_of=datetime(2026, 9, 29, 3, 0, tzinfo=UTC),
        )


@pytest.mark.asyncio
async def test_collector_rejects_symbol_mismatch() -> None:
    collector = EvidenceCollector(
        sources=[
            FakeSource(
                [
                    item(
                        "news:wrong",
                        published_at=datetime(2026, 9, 29, 1, 0, tzinfo=UTC),
                        symbol="6758",
                    )
                ]
            )
        ]
    )

    with pytest.raises(EvidenceCollectionError, match="symbol mismatch"):
        await collector.collect(
            "7203",
            as_of=datetime(2026, 9, 29, 3, 0, tzinfo=UTC),
        )
