from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from universal_stock_skill.data.edinet_csv import EDINETCsvFact


@dataclass(frozen=True)
class FactQuery:
    element_ids: frozenset[str] = frozenset()
    context_ids: frozenset[str] = frozenset()
    relative_years: frozenset[str] = frozenset()
    consolidations: frozenset[str] = frozenset()
    period_types: frozenset[str] = frozenset()


class FactSet:
    """Provider-neutral query helper over EDINET facts.

    Matching primarily by element/context identifiers keeps deterministic
    extraction separate from human-readable labels and LLM interpretation.
    """

    def __init__(self, facts: Iterable[EDINETCsvFact]) -> None:
        self._facts = tuple(facts)

    def query(self, query: FactQuery) -> list[EDINETCsvFact]:
        return [
            fact
            for fact in self._facts
            if self._matches(fact, query)
        ]

    def unique_numeric(self, query: FactQuery) -> Decimal:
        candidates = [
            fact
            for fact in self.query(query)
            if fact.numeric_value is not None
        ]

        if not candidates:
            raise LookupError("no numeric fact matched the query")
        if len(candidates) != 1:
            locations = ", ".join(
                f"{fact.source_file}:{fact.row_number}"
                for fact in candidates
            )
            raise LookupError(
                f"expected one numeric fact, found {len(candidates)} at {locations}"
            )

        value = candidates[0].numeric_value
        assert value is not None
        return value

    @staticmethod
    def _matches(fact: EDINETCsvFact, query: FactQuery) -> bool:
        return (
            (not query.element_ids or fact.element_id in query.element_ids)
            and (not query.context_ids or fact.context_id in query.context_ids)
            and (not query.relative_years or fact.relative_year in query.relative_years)
            and (
                not query.consolidations
                or fact.consolidation in query.consolidations
            )
            and (not query.period_types or fact.period_type in query.period_types)
        )
