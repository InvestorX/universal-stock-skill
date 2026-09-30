from __future__ import annotations

from datetime import datetime
from typing import Protocol

from universal_stock_skill.analysis.models import FinancialSnapshot
from universal_stock_skill.evidence import SourceRecord


class FinancialDataSource(Protocol):
    async def get_snapshot(self, symbol: str, as_of: datetime) -> FinancialSnapshot:
        ...


class DisclosureDataSource(Protocol):
    async def list_disclosures(
        self,
        symbol: str,
        *,
        start: datetime,
        end: datetime,
    ) -> list[SourceRecord]:
        ...


class PriceDataSource(Protocol):
    async def get_price(self, symbol: str, as_of: datetime) -> float:
        ...
