from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

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


class MappingMatchType(StrEnum):
    STANDARD_EXACT = "standard_exact"
    EXTENSION_FALLBACK = "extension_fallback"


@dataclass(frozen=True)
class ElementAlias:
    element_id: str
    accounting_standard: AccountingStandard
    priority: int = 100
    expected_period_type: str | None = None
    semantic_note: str | None = None


@dataclass(frozen=True)
class ExtensionRule:
    contains_any: tuple[str, ...]
    excluded_substrings: tuple[str, ...] = ()
    required_suffixes: tuple[str, ...] = (
        "SummaryOfBusinessResults",
        "KeyFinancialData",
    )
    priority: int = 50
    expected_period_type: str | None = None
    semantic_note: str | None = None

    def matches(self, fact: EDINETCsvFact) -> bool:
        if not _is_company_extension(fact.element_id):
            return False

        local_name = _local_name(fact.element_id)
        if self.required_suffixes and not local_name.endswith(self.required_suffixes):
            return False
        if not any(token in local_name for token in self.contains_any):
            return False
        return not any(token in local_name for token in self.excluded_substrings)


class CanonicalFinancialFact(BaseModel):
    metric: CanonicalMetric
    value: Decimal
    unit: str
    accounting_standard: AccountingStandard
    match_type: MappingMatchType
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


Candidate = tuple[int, EDINETCsvFact, ElementAlias]


class CanonicalFinancialMapper:
    def __init__(
        self,
        mappings: dict[CanonicalMetric, tuple[ElementAlias, ...]],
        extension_rules: dict[CanonicalMetric, tuple[ExtensionRule, ...]] | None = None,
    ) -> None:
        self._mappings = mappings
        self._extension_rules = extension_rules or {}

    def resolve_metric(
        self,
        facts: Iterable[EDINETCsvFact],
        metric: CanonicalMetric,
        *,
        current_year_only: bool = True,
        consolidation: ConsolidationPreference = ConsolidationPreference.AUTO,
    ) -> CanonicalFinancialFact | None:
        fact_list = tuple(facts)
        exact = self._exact_candidates(
            fact_list,
            metric,
            current_year_only=current_year_only,
            consolidation=consolidation,
        )
        if exact:
            return _select_candidate(
                exact,
                metric,
                match_type=MappingMatchType.STANDARD_EXACT,
            )

        fallback = self._extension_candidates(
            fact_list,
            metric,
            current_year_only=current_year_only,
            consolidation=consolidation,
        )
        if fallback:
            return _select_candidate(
                fallback,
                metric,
                match_type=MappingMatchType.EXTENSION_FALLBACK,
            )

        return None

    def _exact_candidates(
        self,
        facts: tuple[EDINETCsvFact, ...],
        metric: CanonicalMetric,
        *,
        current_year_only: bool,
        consolidation: ConsolidationPreference,
    ) -> list[Candidate]:
        aliases = self._mappings.get(metric, ())
        alias_by_id = {alias.element_id: alias for alias in aliases}
        candidates: list[Candidate] = []

        for fact in facts:
            alias = alias_by_id.get(fact.element_id)
            if alias is None or not _eligible(
                fact,
                current_year_only=current_year_only,
                consolidation=consolidation,
            ):
                continue
            candidates.append(
                (
                    _candidate_score(fact, alias, consolidation=consolidation),
                    fact,
                    alias,
                )
            )

        return candidates

    def _extension_candidates(
        self,
        facts: tuple[EDINETCsvFact, ...],
        metric: CanonicalMetric,
        *,
        current_year_only: bool,
        consolidation: ConsolidationPreference,
    ) -> list[Candidate]:
        rules = self._extension_rules.get(metric, ())
        candidates: list[Candidate] = []
        inferred_standard = infer_accounting_standard(facts)

        for fact in facts:
            if not _eligible(
                fact,
                current_year_only=current_year_only,
                consolidation=consolidation,
            ):
                continue

            for rule in rules:
                if not rule.matches(fact):
                    continue
                alias = ElementAlias(
                    element_id=fact.element_id,
                    accounting_standard=(
                        _infer_accounting_standard(fact.element_id)
                        if _infer_accounting_standard(fact.element_id)
                        != AccountingStandard.UNKNOWN
                        else inferred_standard
                    ),
                    priority=rule.priority,
                    expected_period_type=rule.expected_period_type,
                    semantic_note=rule.semantic_note,
                )
                candidates.append(
                    (
                        _candidate_score(fact, alias, consolidation=consolidation),
                        fact,
                        alias,
                    )
                )
                break

        return candidates

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


def _eligible(
    fact: EDINETCsvFact,
    *,
    current_year_only: bool,
    consolidation: ConsolidationPreference,
) -> bool:
    if fact.numeric_value is None:
        return False
    if current_year_only and not _is_current_year(fact):
        return False
    return _scope_allowed(fact, consolidation)


def _select_candidate(
    candidates: list[Candidate],
    metric: CanonicalMetric,
    *,
    match_type: MappingMatchType,
) -> CanonicalFinancialFact:
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
        match_type=match_type,
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


def _local_name(element_id: str) -> str:
    return element_id.split(":", maxsplit=1)[-1]


def _is_company_extension(element_id: str) -> bool:
    prefix = element_id.split(":", maxsplit=1)[0]
    return "-asr_" in prefix


def infer_accounting_standard(
    facts: Iterable[EDINETCsvFact],
) -> AccountingStandard:
    current = [fact for fact in facts if _is_current_year(fact)]
    element_ids = [fact.element_id for fact in current]

    if any("USGAAP" in item or item.startswith("us-gaap:") for item in element_ids):
        return AccountingStandard.USGAAP
    if any("IFRS" in item or item.startswith("ifrs-full:") for item in element_ids):
        return AccountingStandard.IFRS
    if current:
        return AccountingStandard.JGAAP
    return AccountingStandard.UNKNOWN


def _infer_accounting_standard(element_id: str) -> AccountingStandard:
    local_name = _local_name(element_id)
    if "IFRS" in local_name or element_id.startswith("ifrs-full:"):
        return AccountingStandard.IFRS
    if "USGAAP" in local_name or element_id.startswith("us-gaap:"):
        return AccountingStandard.USGAAP
    return AccountingStandard.UNKNOWN


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
