from __future__ import annotations

from datetime import UTC, datetime

import pytest

from universal_stock_skill.analysis import (
    PeerAnalysisOrchestrator,
    PeerComparisonError,
)


AS_OF = datetime(2026, 9, 29, 12, 0, tzinfo=UTC)


class FakeStockOrchestrator:
    def __init__(self, bundles):
        self.bundles = bundles
        self.calls: list[tuple[str, datetime, int]] = []

    async def analyze(self, symbol: str, *, as_of: datetime, years: int = 5):
        self.calls.append((symbol, as_of, years))
        return self.bundles[symbol]


@pytest.mark.asyncio
async def test_peer_orchestrator_uses_same_as_of_and_preserves_order(monkeypatch):
    class Bundle:
        def __init__(self, symbol):
            self.symbol = symbol
            self.requested_as_of = AS_OF

    subject = Bundle("7203")
    honda = Bundle("7267")
    nissan = Bundle("7201")
    stock = FakeStockOrchestrator({"7203": subject, "7267": honda, "7201": nissan})

    class Comparison:
        pass

    captured = {}

    def fake_build(subject_bundle, peers):
        captured["subject"] = subject_bundle
        captured["peers"] = peers
        return Comparison()

    monkeypatch.setattr(
        "universal_stock_skill.analysis.peer_orchestrator.build_peer_comparison",
        fake_build,
    )

    monkeypatch.setattr(
        "universal_stock_skill.analysis.peer_orchestrator.PeerAnalysisResult",
        lambda **kwargs: type("Result", (), kwargs)(),
    )
    orchestrator = PeerAnalysisOrchestrator(stock)  # type: ignore[arg-type]
    result = await orchestrator.analyze(
        "7203",
        peer_symbols=["7267", "7201"],
        as_of=AS_OF,
        years=3,
    )

    assert stock.calls == [
        ("7203", AS_OF, 3),
        ("7267", AS_OF, 3),
        ("7201", AS_OF, 3),
    ]
    assert captured["subject"] is subject
    assert captured["peers"] == [honda, nissan]
    assert result.subject is subject
    assert result.peers == [honda, nissan]


@pytest.mark.asyncio
async def test_peer_orchestrator_rejects_duplicate_symbols_before_io():
    stock = FakeStockOrchestrator({})
    orchestrator = PeerAnalysisOrchestrator(stock)  # type: ignore[arg-type]

    with pytest.raises(PeerComparisonError, match="unique"):
        await orchestrator.analyze(
            "7203",
            peer_symbols=["7267", "7203"],
            as_of=AS_OF,
        )

    assert stock.calls == []


@pytest.mark.asyncio
async def test_peer_orchestrator_requires_peer():
    stock = FakeStockOrchestrator({})
    orchestrator = PeerAnalysisOrchestrator(stock)  # type: ignore[arg-type]

    with pytest.raises(PeerComparisonError, match="at least one"):
        await orchestrator.analyze("7203", peer_symbols=[], as_of=AS_OF)

    assert stock.calls == []
