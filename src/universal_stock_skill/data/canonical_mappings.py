from __future__ import annotations

from universal_stock_skill.data.canonical import (
    AccountingStandard,
    CanonicalFinancialMapper,
    CanonicalMetric,
    ElementAlias,
    ExtensionRule,
)


def _a(
    element_id: str,
    standard: AccountingStandard,
    *,
    priority: int = 100,
    period: str | None = None,
    note: str | None = None,
) -> ElementAlias:
    return ElementAlias(
        element_id=element_id,
        accounting_standard=standard,
        priority=priority,
        expected_period_type=period,
        semantic_note=note,
    )


STANDARD_EDINET_MAPPINGS: dict[CanonicalMetric, tuple[ElementAlias, ...]] = {
    CanonicalMetric.REVENUE: (
        _a("jpcrp_cor:NetSalesSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:RevenueKeyFinancialData", AccountingStandard.JGAAP, priority=150, period="期間"),
        _a("jppfs_cor:NetSales", AccountingStandard.JGAAP, priority=125, period="期間"),
        _a(
            "jppfs_cor:NetSalesOfCompletedConstructionContractsCNS",
            AccountingStandard.JGAAP,
            priority=125,
            period="期間",
        ),
        _a("jpcrp_cor:OperatingRevenue1SummaryOfBusinessResults", AccountingStandard.JGAAP, priority=140, period="期間"),
        _a("jpcrp_cor:OperatingRevenue2SummaryOfBusinessResults", AccountingStandard.JGAAP, priority=140, period="期間"),
        _a("jpcrp_cor:GrossOperatingRevenueSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=135, period="期間"),
        _a(
            "jpcrp_cor:OrdinaryIncomeSummaryOfBusinessResults",
            AccountingStandard.JGAAP,
            priority=130,
            period="期間",
            note=(
                "Industry-specific revenue proxy: ordinary income is used by some "
                "financial institutions and is not directly comparable with net sales."
            ),
        ),
        _a("jpcrp_cor:RevenueIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:RevenuesUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:RevenueUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=155, period="期間"),
    ),
    CanonicalMetric.OPERATING_INCOME: (
        _a("jppfs_cor:OperatingIncome", AccountingStandard.JGAAP, priority=170, period="期間"),
        _a("jpigp_cor:OperatingProfitLossIFRS", AccountingStandard.IFRS, priority=170, period="期間"),
        _a("jpcrp_cor:OperatingIncomeLossUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.PROFIT_BEFORE_TAX: (
        _a("jppfs_cor:IncomeBeforeIncomeTaxes", AccountingStandard.JGAAP, priority=170, period="期間"),
        _a("jpcrp_cor:ProfitLossBeforeTaxIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpigp_cor:ProfitLossBeforeTaxIFRS", AccountingStandard.IFRS, priority=170, period="期間"),
        _a("jpcrp_cor:ProfitLossBeforeTaxUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.NET_INCOME: (
        _a("jppfs_cor:ProfitLossAttributableToOwnersOfParent", AccountingStandard.JGAAP, priority=180, period="期間"),
        _a("jpcrp_cor:ProfitLossAttributableToOwnersOfParentSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=170, period="期間"),
        _a("jpcrp_cor:NetIncomeLossSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:ProfitLossAttributableToOwnersOfParentIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=170, period="期間"),
        _a("jpcrp_cor:ProfitLossIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=150, period="期間"),
        _a("jpcrp_cor:NetIncomeLossAttributableToOwnersOfParentUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=170, period="期間"),
    ),
    CanonicalMetric.TOTAL_ASSETS: (
        _a("jpcrp_cor:TotalAssetsSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="時点"),
        _a("jpcrp_cor:TotalAssetsIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="時点"),
        _a("jpcrp_cor:TotalAssetsUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="時点"),
    ),
    CanonicalMetric.NET_ASSETS: (
        _a("jpcrp_cor:NetAssetsSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="時点"),
        _a("jpcrp_cor:EquityAttributableToOwnersOfParentIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="時点"),
        _a("jpcrp_cor:EquityAttributableToOwnersOfParentUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="時点"),
        _a(
            "jpcrp_cor:EquityIncludingPortionAttributableToNonControllingInterestUSGAAPSummaryOfBusinessResults",
            AccountingStandard.USGAAP,
            priority=140,
            period="時点",
            note="Includes the portion attributable to non-controlling interests.",
        ),
    ),
    CanonicalMetric.EPS: (
        _a("jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:BasicEarningsLossPerShareIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:BasicEarningsLossPerShareUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.DILUTED_EPS: (
        _a("jpcrp_cor:DilutedEarningsPerShareSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:DilutedEarningsLossPerShareIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:DilutedEarningsLossPerShareUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.BPS: (
        _a("jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="時点"),
        _a(
            "jpcrp_cor:EquityToAssetRatioIFRSSummaryOfBusinessResults",
            AccountingStandard.IFRS,
            priority=160,
            period="時点",
            note=(
                "EDINET summary taxonomy naming is counterintuitive here; this "
                "element is used as the IFRS per-share equity/BPS value."
            ),
        ),
        _a("jpcrp_cor:EquityAttributableToOwnersOfParentPerShareUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="時点"),
    ),
    CanonicalMetric.ROE_OFFICIAL: (
        _a("jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160),
        _a("jpcrp_cor:RateOfReturnOnEquityIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160),
        _a("jpcrp_cor:RateOfReturnOnEquityUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160),
    ),
    CanonicalMetric.EQUITY_RATIO_OFFICIAL: (
        _a("jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160),
        _a("jpcrp_cor:RatioOfOwnersEquityToGrossAssetsIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160),
        _a("jpcrp_cor:EquityToAssetRatioUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160),
    ),
    CanonicalMetric.CF_OPERATING: (
        _a("jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInOperatingActivitiesIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInOperatingActivitiesUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.CF_INVESTING: (
        _a("jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInInvestingActivitiesIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInInvestingActivitiesUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.CF_FINANCING: (
        _a("jpcrp_cor:NetCashProvidedByUsedInFinancingActivitiesSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInFinancingActivitiesIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="期間"),
        _a("jpcrp_cor:CashFlowsFromUsedInFinancingActivitiesUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="期間"),
    ),
    CanonicalMetric.CASH: (
        _a("jpcrp_cor:CashAndCashEquivalentsSummaryOfBusinessResults", AccountingStandard.JGAAP, priority=160, period="時点"),
        _a("jpcrp_cor:CashAndCashEquivalentsIFRSSummaryOfBusinessResults", AccountingStandard.IFRS, priority=160, period="時点"),
        _a("jpcrp_cor:CashAndCashEquivalentsUSGAAPSummaryOfBusinessResults", AccountingStandard.USGAAP, priority=160, period="時点"),
    ),
    CanonicalMetric.INCOME_TAXES: (
        _a("jppfs_cor:IncomeTaxes", AccountingStandard.JGAAP, priority=170, period="期間"),
        _a("ifrs-full:IncomeTaxExpenseContinuingOperations", AccountingStandard.IFRS, priority=170, period="期間"),
        _a("jpigp_cor:IncomeTaxExpenseIFRS", AccountingStandard.IFRS, priority=160, period="期間"),
    ),
    CanonicalMetric.CAPEX_TOTAL: (
        _a(
            "jppfs_cor:PurchaseOfPropertyPlantAndEquipmentAndIntangibleAssetsInvCF",
            AccountingStandard.JGAAP,
            priority=180,
            period="期間",
        ),
    ),
    CanonicalMetric.CAPEX_PPE: (
        _a(
            "jppfs_cor:PurchaseOfPropertyPlantAndEquipmentInvCF",
            AccountingStandard.JGAAP,
            priority=170,
            period="期間",
        ),
        _a(
            "jpigp_cor:PurchaseOfPropertyPlantAndEquipmentInvCFIFRS",
            AccountingStandard.IFRS,
            priority=170,
            period="期間",
        ),
        _a(
            "ifrs-full:PurchaseOfPropertyPlantAndEquipmentClassifiedAsInvestingActivities",
            AccountingStandard.IFRS,
            priority=165,
            period="期間",
        ),
    ),
    CanonicalMetric.CAPEX_INTANGIBLE: (
        _a(
            "jppfs_cor:PurchaseOfIntangibleAssetsInvCF",
            AccountingStandard.JGAAP,
            priority=170,
            period="期間",
        ),
        _a(
            "jpigp_cor:PurchaseOfIntangibleAssetsInvCFIFRS",
            AccountingStandard.IFRS,
            priority=170,
            period="期間",
        ),
        _a(
            "ifrs-full:PurchaseOfIntangibleAssetsClassifiedAsInvestingActivities",
            AccountingStandard.IFRS,
            priority=165,
            period="期間",
        ),
    ),
}


EXTENSION_EDINET_MAPPINGS: dict[CanonicalMetric, tuple[ExtensionRule, ...]] = {
    CanonicalMetric.REVENUE: (
        ExtensionRule(
            contains_any=("Revenue", "NetSales", "Sales"),
            excluded_substrings=(
                "Intersegment",
                "Segment",
                "Cost",
                "Expense",
                "Expenses",
                "Gain",
                "Loss",
                "Allowance",
                "Commission",
                "Refund",
                "Proceeds",
                "PerShare",
                "Ratio",
            ),
            priority=60,
            expected_period_type="期間",
            semantic_note=(
                "Matched a company-specific extension taxonomy element with a "
                "curated revenue fallback rule."
            ),
        ),
    ),
    CanonicalMetric.OPERATING_INCOME: (
        ExtensionRule(
            contains_any=(
                "OperatingIncome",
                "OperatingProfit",
                "BusinessProfit",
                "CoreOperatingIncome",
                "ProfitFromBusinessActivities",
            ),
            excluded_substrings=("Segment", "Margin", "Ratio", "PerShare"),
            priority=60,
            expected_period_type="期間",
            semantic_note=(
                "Matched a company-specific extension taxonomy element with a "
                "curated operating-income fallback rule."
            ),
        ),
    ),
    CanonicalMetric.NET_INCOME: (
        ExtensionRule(
            contains_any=("Profit",),
            excluded_substrings=(
                "Ordinary",
                "Operating",
                "BeforeTax",
                "GrossProfit",
                "Equity",
                "Earnings",
                "BusinessProfit",
                "Segment",
                "Margin",
                "Ratio",
                "PerShare",
            ),
            required_suffixes=("SummaryOfBusinessResults",),
            priority=55,
            expected_period_type="期間",
            semantic_note=(
                "Matched a company-specific extension taxonomy element with a "
                "curated net-income fallback rule."
            ),
        ),
    ),
}


DEFAULT_CANONICAL_MAPPER = CanonicalFinancialMapper(
    STANDARD_EDINET_MAPPINGS,
    EXTENSION_EDINET_MAPPINGS,
)
