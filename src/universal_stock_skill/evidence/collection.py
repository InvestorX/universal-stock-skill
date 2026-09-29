from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field

from universal_stock_skill.evidence.guard import PointInTimeGuard
from universal_stock_skill.evidence.models import SourceRecord


class EvidenceItem(BaseModel):
    record: SourceRecord
    symbol: str = Field(min_length=1)
    excerpt: str = ""
    tags: list[str] = Field(default_factory=list)


class EvidenceSource(Protocol):
    async def search(
        self,
        symbol: str,
        *,
        as_of: datetime,
        limit: int = 20,
    ) -> list[EvidenceItem]:
        ...


class EvidenceCollectionError(ValueError):
    pass


@dataclass
class EvidenceCollector:
    sources: Sequence[EvidenceSource]

    async def collect(
        self,
        symbol: str,
        *,
        as_of: datetime,
        limit_per_source: int = 20,
    ) -> list[EvidenceItem]:
        if limit_per_source < 1:
            raise ValueError("limit_per_source must be >= 1")

        normalized_symbol = symbol.strip().upper()
        guard = PointInTimeGuard(as_of)
        collected: list[EvidenceItem] = []

        for source in self.sources:
            items = await source.search(
                normalized_symbol,
                as_of=as_of,
                limit=limit_per_source,
            )
            for item in items:
                if item.symbol.strip().upper() != normalized_symbol:
                    raise EvidenceCollectionError(
                        "evidence source returned a symbol mismatch: "
                        f"expected {normalized_symbol}, got {item.symbol}"
                    )
                guard.validate(item.record)
                collected.append(item)

        deduplicated: dict[str, EvidenceItem] = {}
        for item in collected:
            key = item.record.content_hash or item.record.source_id
            existing = deduplicated.get(key)
            if existing is None:
                deduplicated[key] = item
                continue

            if item.record.published_at > existing.record.published_at:
                deduplicated[key] = item
                continue

            if (
                item.record.published_at == existing.record.published_at
                and item.record.source_id < existing.record.source_id
            ):
                deduplicated[key] = item

        return sorted(
            deduplicated.values(),
            key=lambda item: (
                -item.record.published_at.timestamp(),
                item.record.source_id,
            ),
        )
