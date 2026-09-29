from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceRef(BaseModel):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str | None = None
    published_at: datetime | None = None


class StockAnalysisReport(BaseModel):
    summary: str
    earnings: str
    profitability: str
    financial_position: str
    cash_flow: str
    valuation: str
    growth_drivers: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
