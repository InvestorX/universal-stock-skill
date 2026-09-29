from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimKind(StrEnum):
    FACT = "fact"
    CALCULATION = "calculation"
    INTERPRETATION = "interpretation"
    ASSUMPTION = "assumption"


class EvidenceRef(BaseModel):
    source_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    url: str | None = None
    published_at: datetime | None = None


class GroundedClaim(BaseModel):
    claim_id: str = Field(min_length=1)
    text: str = Field(min_length=1)
    kind: ClaimKind
    evidence_ids: list[str] = Field(default_factory=list)
    metric_ids: list[str] = Field(default_factory=list)


class StockAnalysisReport(BaseModel):
    symbol: str | None = None
    as_of: datetime | None = None
    summary: str
    earnings: str
    profitability: str
    financial_position: str
    cash_flow: str
    valuation: str
    peer_comparison: str | None = None
    growth_drivers: list[str] = Field(default_factory=list)
    catalysts: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    scenarios: list[str] = Field(default_factory=list)
    claims: list[GroundedClaim] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    evidence: list[EvidenceRef] = Field(default_factory=list)
