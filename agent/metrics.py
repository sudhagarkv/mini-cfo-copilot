from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Optional, Dict
from .data import load_csvs, to_usd

def _prep():
    actuals, budget, fx, cash = load_csvs()
    actuals_usd = to_usd(actuals, fx)
    budget_usd  = to_usd(budget,  fx)
    return actuals_usd, budget_usd, cash

def revenue_vs_budget(month: pd.Timestamp) -> Dict[str, float]:
    a, b, _ = _prep()
    a_m = a[(a["month"] == month) & (a["account_category"] == "Revenue")]
    b_m = b[(b["month"] == month) & (b["account_category"] == "Revenue")]
    actual   = a_m["amount_usd"].sum()
    budgeted = b_m["amount_usd"].sum()
    variance = actual - budgeted
    pct = (variance / budgeted) * 100 if budgeted != 0 else np.nan
    return {
        "month": month,
        "actual_usd": float(actual),
        "budget_usd": float(budgeted),
        "variance_usd": float(variance),
        "variance_pct": float(pct) if pd.notna(pct) else float("nan"),
    }

def gross_margin_series(last_n: Optional[int] = None) -> pd.DataFrame:
    a, _, _ = _prep()
    rev  = a[a["account_category"] == "Revenue"].groupby("month")["amount_usd"].sum()
    cogs = a[a["account_category"] == "COGS"].groupby("month")["amount_usd"].sum()
    # align indices
    idx = rev.index.union(cogs.index)
    rev  = rev.reindex(idx,  fill_value=0.0)
    cogs = cogs.reindex(idx, fill_value=0.0)
    gm = ((rev - cogs) / rev.replace(0, np.nan)) * 100
    df = gm.to_frame("gross_margin_pct").reset_index().sort_values("month")
    if last_n:
        df = df.tail(last_n)
    return df

def opex_breakdown(month: pd.Timestamp) -> pd.DataFrame:
    a, _, _ = _prep()
    m = a[(a["month"] == month) & (a["account_category"].str.startswith("Opex:"))]
    out = (
        m.groupby("account_category")["amount_usd"].sum()
         .reset_index().rename(columns={"amount_usd":"total_usd"})
         .sort_values("total_usd", ascending=False)
    )
    out["category"] = out["account_category"].str.replace(r"^Opex:\s*", "", regex=True)
    return out[["category", "total_usd"]]

def ebitda_series() -> pd.DataFrame:
    a, _, _ = _prep()
    by = a.groupby(["month","account_category"])["amount_usd"].sum().unstack(fill_value=0)
    rev  = by.get("Revenue", 0.0)
    cogs = by.get("COGS",    0.0)
    opex_cols = [c for c in by.columns if isinstance(c, str) and c.startswith("Opex:")]
    opex_total = by[opex_cols].sum(axis=1) if opex_cols else 0.0
    ebitda = (rev - cogs - opex_total).rename("ebitda_usd")
    return ebitda.reset_index()

def cash_runway_months(reference_month: Optional[pd.Timestamp] = None) -> Dict[str, float]:
    _, _, cash = _prep()
    e_df = ebitda_series().sort_values("month")
    if reference_month is None:
        reference_month = cash["month"].max()
    recent = e_df[e_df["month"] <= reference_month].tail(3)
    burn = (-recent["ebitda_usd"]).clip(lower=0).mean()  # positive burn
    total_cash = cash[cash["month"] == reference_month]["cash_usd"].sum()
    runway = (total_cash / burn) if burn and burn > 0 else float("inf")
    return {
        "reference_month": pd.to_datetime(reference_month),
        "cash_usd": float(total_cash),
        "avg_monthly_burn_usd": float(burn),
        "runway_months": float(runway),
    }
