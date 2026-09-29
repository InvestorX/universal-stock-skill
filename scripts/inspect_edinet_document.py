from __future__ import annotations

import argparse
import asyncio
import json
import os

from universal_stock_skill.data import (
    EDINETCanonicalPipeline,
    EDINETClient,
    EDINETConfig,
    EDINETDocument,
)


async def run(doc_id: str, api_key: str) -> None:
    client = EDINETClient(EDINETConfig(api_key=api_key))
    document = EDINETDocument(docID=doc_id, csvFlag="1")
    canonical = await EDINETCanonicalPipeline(client).load_document(document)

    print(
        json.dumps(
            canonical.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download one EDINET CSV document and inspect canonical mappings."
    )
    parser.add_argument("doc_id")
    args = parser.parse_args()

    api_key = os.environ.get("EDINET_API_KEY")
    if not api_key:
        parser.error("EDINET_API_KEY is required")

    asyncio.run(run(args.doc_id, api_key))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
