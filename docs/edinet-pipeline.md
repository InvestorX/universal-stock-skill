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
