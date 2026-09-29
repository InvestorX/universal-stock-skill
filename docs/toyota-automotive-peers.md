# Toyota automotive peer regression

[日本語](toyota-automotive-peers.ja.md)

## Goal

Extend the Toyota 7203 real-company regression with Honda 7267 and Nissan 7201 peer rows using official annual results.

The comparison is built for the common period end March 31, 2026.

Issuer fiscal labels differ:

- Toyota: FY2026
- Honda: fiscal year ended March 31, 2026
- Nissan: FY2025

The runtime therefore aligns on period end rather than issuer fiscal-year label.

## Reference rows

Honda 7267 uses IFRS results for the year ended March 31, 2026.

Frozen values include sales revenue JPY 21,796,610 million, operating loss JPY 414,346 million, parent-attributable loss JPY 423,941 million, operating margin -1.9%, ROE -3.5%, EPS -JPY 106.06, BPS JPY 3,035.91, and 3,892,580,441 end-of-year shares outstanding excluding treasury stock.

Honda cash-FCF reference uses operating cash flow JPY 1,135,261 million less additions to PPE JPY 612,065 million and intangible assets JPY 285,480 million.

Nissan 7201 labels the year ended March 31, 2026 as FY2025.

Frozen values include net sales JPY 12,007,888 million, operating income JPY 58,005 million, parent-attributable net loss JPY 533,095 million, operating margin 0.5%, ROE -10.9%, EPS -JPY 152.58, BPS JPY 1,372.56, 3,496,382,520 end-of-year shares outstanding excluding treasury stock, and consolidated operating cash flow JPY 753,687 million.

## Loss-making PER policy

Honda and Nissan both have negative EPS for the common annual period.

The peer reference therefore sets PER to unavailable instead of returning a negative PER. This avoids misreading a negative numerical multiple as a conventional low valuation multiple.

PBR remains available because BPS is positive.

## FCF comparability

Honda has a comparable consolidated cash-FCF reference.

Nissan FCF yield is intentionally unavailable because its published automobile-business FCF is not treated as directly equivalent to the consolidated cash-FCF definition used for Toyota and Honda.

The definition gap is preserved as a limitation instead of forcing unlike measures into one comparison.

## Market-price policy

Historical prices are not frozen in the fixture. Example Toyota JPY 3,000, Honda JPY 1,500, and Nissan JPY 350 values are explicit regression inputs only.

Production comparison should use point-in-time MarketSnapshot values for all companies at the requested timestamp.

## Grounding IDs

The Toyota peer AnalysisContext exposes deterministic IDs such as:

- peer:7203:revenue_yoy
- peer:7267:revenue_yoy
- peer:7201:revenue_yoy
- peer:7203:operating_margin
- peer:7267:operating_margin
- peer:7201:operating_margin
- peer:7203:roe
- peer:7267:roe
- peer:7201:roe

Official peer evidence IDs include:

- peer:7267:ir:fy2026-results
- peer:7267:ir:fy2026-cashflow-reference
- peer:7201:ir:fy2025-results

The final peer report uses these IDs rather than asking the model to recalculate the comparison.

## Inspect the context

Use:

    python scripts/inspect_toyota_peer_context.py \
      --toyota-price 3000 \
      --honda-price 1500 \
      --nissan-price 350 \
      --as-of 2026-09-29T15:30:00+09:00
