from datetime import UTC, date, datetime

import httpx
import pytest

from universal_stock_skill.data import EDINETClient, EDINETConfig


def build_transport() -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.params["Subscription-Key"] == "test-key"

        if request.url.path.endswith("/documents.json"):
            assert request.url.params["date"] == "2026-01-05"
            assert request.url.params["type"] == "2"
            return httpx.Response(
                200,
                json={
                    "metadata": {"status": "200", "message": "OK"},
                    "results": [
                        {
                            "docID": "S100TEST",
                            "edinetCode": "E00001",
                            "secCode": "72030",
                            "filerName": "Demo Corporation",
                            "docTypeCode": "120",
                            "submitDateTime": "2026-01-05 15:30",
                            "docDescription": "Annual Securities Report",
                            "xbrlFlag": "1",
                            "pdfFlag": "1",
                            "csvFlag": "1",
                        }
                    ],
                },
            )

        if request.url.path.endswith("/documents/S100TEST"):
            assert request.url.params["type"] == "5"
            return httpx.Response(200, content=b"fake-zip")

        return httpx.Response(404)

    return httpx.MockTransport(handler)


@pytest.mark.asyncio
async def test_list_documents_and_convert_to_evidence() -> None:
    client = EDINETClient(
        EDINETConfig(api_key="test-key"),
        transport=build_transport(),
    )

    documents = await client.list_documents(date(2026, 1, 5))

    assert len(documents) == 1
    document = documents[0]
    assert document.doc_id == "S100TEST"
    assert document.sec_code == "72030"

    source = document.to_source_record(
        retrieved_at=datetime(2026, 1, 6, tzinfo=UTC),
    )
    assert source.source_id == "edinet:S100TEST"
    assert source.published_at.isoformat() == "2026-01-05T15:30:00+09:00"


@pytest.mark.asyncio
async def test_download_csv_document() -> None:
    client = EDINETClient(
        EDINETConfig(api_key="test-key"),
        transport=build_transport(),
    )

    payload = await client.download_document("S100TEST", document_type=5)
    assert payload == b"fake-zip"


@pytest.mark.asyncio
async def test_invalid_document_type_is_rejected() -> None:
    client = EDINETClient(EDINETConfig(api_key="test-key"))

    with pytest.raises(ValueError):
        await client.download_document("S100TEST", document_type=9)
