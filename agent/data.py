import pandas as pd
from pathlib import Path

FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures"

def load_csvs(fixtures_dir: Path = FIXTURES_DIR):
    actuals = pd.read_csv(fixtures_dir / "actuals.csv", parse_dates=["month"])
    budget  = pd.read_csv(fixtures_dir / "budget.csv",  parse_dates=["month"])
    fx      = pd.read_csv(fixtures_dir / "fx.csv",      parse_dates=["month"])
    cash    = pd.read_csv(fixtures_dir / "cash.csv",    parse_dates=["month"])
    return actuals, budget, fx, cash

def to_usd(df: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    merged = df.merge(fx, on=["month", "currency"], how="left")
    merged["amount_usd"] = merged["amount"] * merged["rate_to_usd"]
    return merged

def month_str(dt):
    return dt.strftime("%B %Y")
