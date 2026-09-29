from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field

from universal_stock_skill.evidence import SourceRecord

JST = ZoneInfo("Asia/Tokyo")


class EDINETDocument(BaseModel):
    doc_id: str = Field(alias="docID")
    edinet_code: str | None = Field(default=None, alias="edinetCode")
    sec_code: str | None = Field(default=None, alias="secCode")
    filer_name: str | None = Field(default=None, alias="filerName")
    fund_code: str | None = Field(default=None, alias="fundCode")
    ordinance_code: str | None = Field(default=None, alias="ordinanceCode")
    form_code: str | None = Field(default=None, alias="formCode")
    doc_type_code: str | None = Field(default=None, alias="docTypeCode")
    period_start: str | None = Field(default=None, alias="periodStart")
    period_end: str | None = Field(default=None, alias="periodEnd")
    submit_date_time: str | None = Field(default=None, alias="submitDateTime")
    doc_description: str | None = Field(default=None, alias="docDescription")
    xbrl_flag: str | None = Field(default=None, alias="xbrlFlag")
    pdf_flag: str | None = Field(default=None, alias="pdfFlag")
    attach_doc_flag: str | None = Field(default=None, alias="attachDocFlag")
    english_doc_flag: str | None = Field(default=None, alias="englishDocFlag")
    csv_flag: str | None = Field(default=None, alias="csvFlag")

    model_config = {"populate_by_name": True}

    def published_at(self) -> datetime:
        if not self.submit_date_time:
            raise ValueError(f"document {self.doc_id} has no submitDateTime")

        parsed = datetime.fromisoformat(self.submit_date_time)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            parsed = parsed.replace(tzinfo=JST)
        return parsed

    def to_source_record(self, *, retrieved_at: datetime | None = None) -> SourceRecord:
        retrieved = retrieved_at or datetime.now(UTC)
        title = self.doc_description or self.filer_name or self.doc_id

        return SourceRecord(
            source_id=f"edinet:{self.doc_id}",
            source_type="filing",
            title=title,
            published_at=self.published_at(),
            retrieved_at=retrieved,
            metadata={
                "doc_id": self.doc_id,
                "edinet_code": self.edinet_code,
                "sec_code": self.sec_code,
                "filer_name": self.filer_name,
                "doc_type_code": self.doc_type_code,
            },
        )


@dataclass(frozen=True)
class EDINETConfig:
    api_key: str
    base_url: str = "https://api.edinet-fsa.go.jp"
    timeout_seconds: float = 60.0


class EDINETClient:
    def __init__(
        self,
        config: EDINETConfig,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.config = config
        self.transport = transport

    def _params(self, **values: str | int) -> dict[str, str | int]:
        return {
            **values,
            "Subscription-Key": self.config.api_key,
        }

    async def list_documents(self, submission_date: date) -> list[EDINETDocument]:
        url = f"{self.config.base_url.rstrip('/')}/api/v2/documents.json"
        params = self._params(date=submission_date.isoformat(), type=2)

        async with httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            payload = response.json()

        results = payload.get("results") or []
        return [EDINETDocument.model_validate(item) for item in results]

    async def download_document(self, doc_id: str, *, document_type: int = 1) -> bytes:
        if document_type not in {1, 2, 3, 4, 5}:
            raise ValueError("document_type must be one of 1, 2, 3, 4, 5")

        url = f"{self.config.base_url.rstrip('/')}/api/v2/documents/{doc_id}"
        params = self._params(type=document_type)

        async with httpx.AsyncClient(
            timeout=self.config.timeout_seconds,
            transport=self.transport,
        ) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.content
