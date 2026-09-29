# EDINET analysis pipeline

[日本語](edinet-pipeline.ja.md)

## Current path

~~~mermaid
flowchart LR
    S[Security code] --> R[AnnualFilingResolver]
    R --> D[Selected EDINET document]
    D --> Z[CSV ZIP download]
    Z --> P[EDINETCsvArchive]
    P --> F[EDINETCsvFact]
    F --> C[CanonicalFinancialMapper]
    C --> CF[CanonicalFinancialSet]
    C --> TS[CanonicalFinancialSeries]
    TS --> TR[YoY / CAGR trends]
    CF --> B[FinancialSnapshot bridge]
    B --> FS[FinancialSnapshot]
    FS --> M[Deterministic stock metrics]
    M --> A[Stock analysis skill]
~~~

## Filing resolution

Annual filing resolution is point-in-time aware.

The resolver:

- normalizes a four-character security code to EDINET's five-character form
- considers annual reports available by the requested as-of timestamp
- selects the newest fiscal period
- follows correction-report parent relationships
- selects the latest reachable correction available by the cutoff
- never uses a correction published after the cutoff

The original and selected document are both preserved.

## Canonical to FinancialSnapshot bridge

EDINET currently supplies these required FinancialSnapshot inputs through canonical metrics:

- revenue
- operating income
- net income
- EPS
- BPS
- operating cash flow

Other inputs still come from dedicated deterministic sources or derivations:

- stock price
- market capitalization
- average equity
- capital expenditure
- NOPAT
- average invested capital

This separation is deliberate. Market data should not be fabricated from filing data, and average balance-sheet values require period-aware derivation.

## Real-document inspection

With an EDINET API key:

~~~bash
export EDINET_API_KEY=...
python scripts/inspect_edinet_document.py S100XXXX
~~~

On Windows PowerShell:

~~~powershell
$env:EDINET_API_KEY="..."
python scripts/inspect_edinet_document.py S100XXXX
~~~

The command downloads EDINET document type 5, parses its XBRL-to-CSV archive, applies canonical mapping, and prints the mapped facts and missing metrics.

It does not invoke an LLM.

If a type=5 ZIP has already been downloaded, no API key is needed:

~~~bash
python scripts/inspect_edinet_csv.py path/to/document.zip
~~~

This is the preferred path for reproducible fixture validation because the exact source archive can be retained locally.


## Historical pipeline

`EDINETCanonicalPipeline.load_document_series(document, years=5)` downloads and parses the filing once, then resolves CurrentYear / PriorNYear facts into a canonical historical series.

This feeds deterministic trend analysis directly; the LLM receives already-aligned periods and calculated growth metrics rather than being asked to infer them from raw rows.


## Single-download bundle

When both current and historical values are required, use:

~~~python
bundle = await pipeline.load_document_bundle(document, years=5)
~~~

The document archive is downloaded and parsed once. The result contains both `current` and `series`, avoiding duplicate EDINET requests.


## FinancialSnapshot readiness preflight

Before building a `FinancialSnapshot`, call `evaluate_snapshot_readiness(current)`.

The filing-side required metrics are:

- revenue
- operating income
- net income
- EPS
- BPS
- operating cash flow

The result reports whether all six are present, which are missing, and which required metrics depend on extension fallback.

This is only the filing-side preflight. Price, market capitalization, average equity, and capital expenditure still come from separate deterministic sources or derivations.
