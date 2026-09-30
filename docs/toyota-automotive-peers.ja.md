# トヨタ自動車Peer Regression

[English](toyota-automotive-peers.md) | **日本語**

## 目的

トヨタ7203の実在企業Regressionへ、Honda 7267とNissan 7201の公式年間決算を使ったPeer比較を追加します。

比較対象期間は共通して2026-03-31終了年度です。

各社の年度ラベルは異なります。

- Toyota: FY2026
- Honda: 2026年3月期
- Nissan: FY2025

そのためRuntimeはFiscal Year名称ではなくperiod_endで期間を揃えます。

## Reference Row

Honda 7267は2026年3月期のIFRS連結決算を使用します。

固定する主な値は、売上収益21,796,610百万円、営業損失414,346百万円、親会社帰属損失423,941百万円、営業利益率-1.9%、ROE -3.5%、EPS -106.06円、BPS 3,035.91円、期末自己株式控除後株式数3,892,580,441株です。

HondaのCash FCF Referenceは、営業CF 1,135,261百万円からPPE取得支出612,065百万円と無形資産取得支出285,480百万円を差し引きます。

Nissan 7201は2026-03-31終了年度をFY2025と表記します。

固定する主な値は、売上高12,007,888百万円、営業利益58,005百万円、親会社帰属純損失533,095百万円、営業利益率0.5%、ROE -10.9%、EPS -152.58円、BPS 1,372.56円、期末自己株式控除後株式数3,496,382,520株、連結営業CF 753,687百万円です。

## 赤字企業のPER

HondaとNissanは共通年度のEPSがマイナスです。

そのためPeer ReferenceではPERを負の数として返さず、利用不可として扱います。負のPERを「PERが低い＝割安」と誤読しないためです。

BPSは正なのでPBRは利用可能です。

## FCFの比較可能性

Hondaは連結営業CFを使ったCash FCF Referenceを作れます。

NissanのFCF Yieldは意図的に利用不可とします。Nissanが公表するAutomobile Business FCFと、Toyota/Hondaで使う連結Cash FCFを同一Metricとして扱わないためです。

定義差を無理に消さず、Comparison Limitationとして保持します。

## 株価の扱い

Fixtureでは過去株価を固定しません。Toyota 3,000円、Honda 1,500円、Nissan 350円などはRegression用の入力です。

本番では同じrequested_as_ofに対する各社MarketSnapshotを使います。

## Grounding ID

Toyota Peer AnalysisContextでは次のような決定論的IDを利用できます。

- peer:7203:revenue_yoy
- peer:7267:revenue_yoy
- peer:7201:revenue_yoy
- peer:7203:operating_margin
- peer:7267:operating_margin
- peer:7201:operating_margin
- peer:7203:roe
- peer:7267:roe
- peer:7201:roe

公式Peer Evidence ID:

- peer:7267:ir:fy2026-results
- peer:7267:ir:fy2026-cashflow-reference
- peer:7201:ir:fy2025-results

LLMへ比較計算をやり直させず、これらのIDでGrounded Reportを作ります。

## Context確認

    python scripts/inspect_toyota_peer_context.py \
      --toyota-price 3000 \
      --honda-price 1500 \
      --nissan-price 350 \
      --as-of 2026-09-29T15:30:00+09:00
