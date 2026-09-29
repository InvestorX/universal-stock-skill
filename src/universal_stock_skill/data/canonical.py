from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Iterable

from pydantic import BaseModel

from universal_stock_skill.data.edinet_csv import EDINETCsvFact


class AccountingStandard(StrEnum):
    JGAAP = "jgaap"
    IFRS = "ifrs"
    USGAAP = "usgaap"
    UNKNOWN = "unknown"


class CanonicalMetric(StrEnum):
    REVENUE = "revenue"
    OPERATING_INCOME = "operating_income"
    PROFIT_BEFORE_TAX = "profit_before_tax"
    NET_INCOME = "net_income"
    TOTAL_ASSETS = "total_assets"
    NET_ASSETS = "net_assets"
    EPS = "eps"
    DILUTED_EPS = "diluted_eps"
    BPS = "bps"
    ROE_OFFICIAL = "roe_official"
    EQUITY_RATIO_OFFICIAL = "equity_ratio_official"
    CF_OPERATING = "cf_operating"
    CF_INVESTING = "cf_investing"
    CF_FINANCING = "cf_financing"
    CASH = "cash"


class ConsolidationPreference(StrEnum):
    AUTO = "auto"
    CONSOLIDATED = "consolidated"
    NON_CONSOLIDATED = "non_consolidated"


@dataclass(frozen=True)
class ElementAlias:
    element_id: str
    accounting_standard: AccountingStandard
    priority: int = 100
    expected_period_type: str | None = None
    semantic_note: str | None = None


class CanonicalFinancialFact(BaseModel):
    metric: CanonicalMetric
    value: Decimal
    unit: str
    accounting_standard: AccountingStandard
    element_id: str
    item_name: str
    context_id: str
    relative_year: str
    consolidation: str
    period_type: str
    source_file: str
    row_number: int
    semantic_note: str | None = None


class CanonicalFinancialSet(BaseModel):
    facts: list[CanonicalFinancialFact]
    missing: list[CanonicalMetric]

    def get(self, metric: CanonicalMetric) -> CanonicalFinancialFact | None:
        return next((fact for fact in self.facts if fact.metric == metric), None)


class CanonicalMappingConflict(ValueError):
    pass


class CanonicalFinancialMapper:
    def __init__(self, mappings: dict[CanonicalMetric, tuple[ElementAlias, ...]]) -> None:
        self._mappings = mappings

    def resolve_metric(
        self,
        facts: Iterable[EDINETCsvFact],
        metric: CanonicalMetric,
        *,
        current_year_only: bool = True,
        consolidation: ConsolidationPreference = ConsolidationPreference.AUTO,
    ) -> CanonicalFinancialFact | None:
        aliases = self._mappings.get(metric, ())
        alias_by_id = {alias.element_id: alias for alias in aliases}
        candidates: list[tuple[int, EDINETCsvFact, ElementAlias]] = []

        for fact in facts:
            alias = alias_by_id.get(fact.element_id)
            if alias is None or fact.numeric_value is None:
                continue
            if current_year_only and not _is_current_year(fact):
                continue
            if not _scope_allowed(fact, consolidation):
                continue

            score = _candidate_score(
                fact,
                alias,
                consolidation=consolidation,
            )
            candidates.append((score, fact, alias))

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                -item[0],
                item[1].element_id,
                item[1].context_id,
                item[1].source_file,
                item[1].row_number,
            )
        )
        best_score = candidates[0][0]
        best = [item for item in candidates if item[0] == best_score]

        values = {(item[1].numeric_value, item[1].unit) for item in best}
        if len(values) > 1:
            locations = ", ".join(
                f"{fact.source_file}:{fact.row_number}={fact.raw_value}"
                for _, fact, _ in best
            )
            raise CanonicalMappingConflict(
                f"conflicting {metric.value} facts at equal priority: {locations}"
            )

        _, fact, alias = best[0]
        value = fact.numeric_value
        assert value is not None

        return CanonicalFinancialFact(
            metric=metric,
            value=value,
            unit=fact.unit,
            accounting_standard=alias.accounting_standard,
            element_id=fact.element_id,
            item_name=fact.item_name,
            context_id=fact.context_id,
            relative_year=fact.relative_year,
            consolidation=fact.consolidation,
            period_type=fact.period_type,
            source_file=fact.source_file,
            row_number=fact.row_number,
            semantic_note=alias.semantic_note,
        )

    def resolve(
        self,
        facts: Iterable[EDINETCsvFact],
        metrics: Iterable[CanonicalMetric] | None = None,
        *,
        current_year_only: bool = True,
        consolidation: ConsolidationPreference = ConsolidationPreference.AUTO,
    ) -> CanonicalFinancialSet:
        fact_list = tuple(facts)
        requested = tuple(metrics or self._mappings.keys())
        resolved: list[CanonicalFinancialFact] = []
        missing: list[CanonicalMetric] = []

        for metric in requested:
            fact = self.resolve_metric(
                fact_list,
                metric,
                current_year_only=current_year_only,
                consolidation=consolidation,
            )
            if fact is None:
                missing.append(metric)
            else:
                resolved.append(fact)

        return CanonicalFinancialSet(facts=resolved, missing=missing)


def _is_current_year(fact: EDINETCsvFact) -> bool:
    relative = fact.relative_year.strip()
    context = fact.context_id
    return relative == "当期" or context.startswith("CurrentYear")


def _is_non_consolidated(fact: EDINETCsvFact) -> bool:
    consolidation = fact.consolidation.strip()
    context = fact.context_id

    if consolidation in {"個別", "単体", "非連結"}:
        return True
    return "NonConsolidated" in context


def _scope_allowed(
    fact: EDINETCsvFact,
    preference: ConsolidationPreference,
) -> bool:
    is_non_consolidated = _is_non_consolidated(fact)
    if preference == ConsolidationPreference.CONSOLIDATED:
        return not is_non_consolidated
    if preference == ConsolidationPreference.NON_CONSOLIDATED:
        return is_non_consolidated
    return True


def _candidate_score(
    fact: EDINETCsvFact,
    alias: ElementAlias,
    *,
    consolidation: ConsolidationPreference,
) -> int:
    score = alias.priority

    if _is_current_year(fact):
        score += 100

    if consolidation == ConsolidationPreference.AUTO:
        score += 40 if not _is_non_consolidated(fact) else 0

    if "Member" not in fact.context_id:
        score += 20

    if alias.expected_period_type and fact.period_type == alias.expected_period_type:
        score += 10

    if fact.context_id.startswith("CurrentYear"):
        score += 5

    return score
