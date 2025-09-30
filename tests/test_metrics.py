import pandas as pd
from agent.metrics import revenue_vs_budget, gross_margin_series

def test_revenue_vs_budget_runs():
    from agent.data import load_csvs
    a, _, _, _ = load_csvs()
    month = pd.to_datetime(a["month"].max())
    res = revenue_vs_budget(month)
    assert "actual_usd" in res and "budget_usd" in res

def test_gm_series_has_pct():
    df = gross_margin_series(last_n=3)
    assert "gross_margin_pct" in df.columns
    assert len(df) <= 3
