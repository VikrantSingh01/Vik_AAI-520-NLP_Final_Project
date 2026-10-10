"""Financial calculations that preserve source period and concept metadata."""

from __future__ import annotations

import numpy as np
import pandas as pd

from faangm_research.schemas import FinancialFact


def financial_panel(facts: list[FinancialFact]) -> pd.DataFrame:
    """Return validated annual facts plus transparent derived measures."""
    records = [fact.model_dump(mode="json") for fact in facts]
    if not records:
        return pd.DataFrame()
    long = pd.DataFrame(records)
    duplicate_keys = ["ticker", "fiscal_year", "metric"]
    if long.duplicated(duplicate_keys).any():
        duplicates = long.loc[
            long.duplicated(duplicate_keys, keep=False), duplicate_keys
        ]
        raise ValueError(f"Duplicate annual facts detected:\n{duplicates}")

    values = long.pivot(
        index=["ticker", "fiscal_year"], columns="metric", values="value"
    )
    values = values.sort_index().reset_index()
    by_company = values.groupby("ticker", group_keys=False)
    values["revenue_growth"] = by_company["revenue"].pct_change(fill_method=None)
    values["operating_margin"] = values["operating_income"] / values["revenue"]
    values["free_cash_flow"] = (
        values["operating_cash_flow"] - values["capital_expenditures"]
    )
    values["fcf_margin"] = values["free_cash_flow"] / values["revenue"]
    values["capex_intensity"] = values["capital_expenditures"] / values["revenue"]
    if "research_and_development" in values:
        values["rd_intensity"] = values["research_and_development"] / values["revenue"]
    else:
        values["rd_intensity"] = np.nan
    return values


def latest_company_metrics(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return panel.copy()
    latest_rows = panel.groupby("ticker")["fiscal_year"].idxmax()
    return panel.loc[latest_rows].sort_values("ticker").reset_index(drop=True)
